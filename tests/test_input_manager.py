import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

from modules.controls import ControlsMenu
from modules.enums import GameState
from modules.input_manager import InputManager


def key(code, text=""):
    return pygame.event.Event(pygame.KEYDOWN, key=code, unicode=text)


def joystick_event(kind, instance, **attributes):
    # SDL still supplies a legacy joystick index on some platforms. Routing
    # must follow the SDL instance ID even if that index points to P2.
    return pygame.event.Event(kind, instance_id=instance, joy=1, **attributes)


def add_device(manager, index):
    assert manager.actions_for(pygame.event.Event(pygame.JOYDEVICEADDED, device_index=index)) == set()


def remove_device(manager, instance):
    assert manager.actions_for(pygame.event.Event(pygame.JOYDEVICEREMOVED, instance_id=instance)) == set()


def device(instance, guid, name):
    return SimpleNamespace(init=lambda: None, get_instance_id=lambda: instance,
                           get_guid=lambda: guid, get_name=lambda: name)


def test_migration_keeps_existing_keys_and_buttons(tmp_path):
    path = tmp_path / "controls.json"
    path.write_text(json.dumps({
        "p1_up": {"key": pygame.K_i, "button": 7},
        "p2_fire": {"key": pygame.K_n, "button": 2},
        "p1_fire": {"key": "unreadable", "button": -1},
    }), encoding="utf-8")
    manager = InputManager(path, False)
    assert manager.bindings["p1_up"]["key"] == pygame.K_i
    assert manager.actions_for(key(pygame.K_i), player_count=1) == {"p1_up"}
    assert manager.actions_for(key(pygame.K_n), player_count=2) == {"p2_fire"}
    assert manager.actions_for(key(pygame.K_SPACE), player_count=1) == {"p1_fire"}
    assert manager.actions_for(pygame.event.Event(pygame.JOYBUTTONDOWN, joy=0, button=7)) == {"p1_up"}
    manager.save()
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 2
    assert InputManager(path, False).bindings == manager.bindings


def test_save_failure_leaves_previous_file_and_no_temporary_files(tmp_path, monkeypatch):
    path = tmp_path / "controls.json"
    manager = InputManager(path, False)
    manager.save()
    before = path.read_bytes()
    manager.remove("p1_left")

    def fail_replace(*args):
        raise OSError("disk write unavailable")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError):
        manager.save()
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]


def test_enter_fire_is_contextual_and_alternates_are_removable(tmp_path):
    manager = InputManager(tmp_path / "controls.json", False)
    assert manager.actions_for(key(pygame.K_RETURN), player_count=1) == {"p1_fire", "menu_accept"}
    assert manager.actions_for(key(pygame.K_RETURN), player_count=2) == {"p2_fire", "menu_accept"}
    assert manager.actions_for(key(pygame.K_PLUS), player_count=2) == {"p2_fire"}
    assert manager.bind_event("p1_fire", key(pygame.K_w), save=False)
    assert manager.conflicts("p1_fire") == ["p1_up"]
    assert manager.actions_for(key(pygame.K_RETURN), player_count=1) == {"menu_accept"}
    manager.remove("p2_fire")
    assert manager.actions_for(key(pygame.K_PLUS), player_count=2) == set()
    assert manager.actions_for(key(pygame.K_p), player_count=2) == {"pause"}
    assert manager.actions_for(key(0, "ü"), player_count=2) == {"special_effect"}
    assert manager.bind_event("special_effect", key(pygame.K_g), save=False)
    assert manager.actions_for(key(0, "ü"), player_count=2) == set()
    assert manager.actions_for(key(pygame.K_g), player_count=2) == {"special_effect"}


def test_devices_route_independently_and_restore_binding_on_hotplug(tmp_path, monkeypatch):
    devices = [device(43, "stick", "T.16000M"), device(44, "throttle", "TWCS")]
    monkeypatch.setattr(pygame.joystick, "Joystick", devices.__getitem__)
    path = tmp_path / "controls.json"
    manager = InputManager(path, False)
    add_device(manager, 0)
    add_device(manager, 1)
    button = joystick_event(pygame.JOYBUTTONDOWN, 44, button=0)
    assert "p2_fire" in manager.actions_for(button, player_count=2)
    manager.set_player("throttle:1", 1)
    assert "p1_fire" in manager.actions_for(button, player_count=2)
    assert "p2_fire" not in manager.actions_for(button, player_count=2)
    assert "p1_fire" in manager.actions_for(
        joystick_event(pygame.JOYBUTTONDOWN, 43, button=0), player_count=2)

    capture = joystick_event(pygame.JOYBUTTONDOWN, 44, button=4)
    assert manager.bind_event("p1_fire", capture, device="throttle:1")
    remove_device(manager, 44)
    assert manager.actions_for(capture, player_count=2) == set()
    devices[1] = device(70, "throttle", "TWCS")
    reopened = InputManager(path, False)
    add_device(reopened, 1)
    assert reopened.actions_for(
        joystick_event(pygame.JOYBUTTONDOWN, 70, button=4), player_count=2) == {"p1_fire"}


def test_identical_devices_can_manually_swap_profiles(tmp_path, monkeypatch):
    devices = [device(3, "same", "Gamepad"), device(4, "same", "Gamepad")]
    monkeypatch.setattr(pygame.joystick, "Joystick", devices.__getitem__)
    manager = InputManager(tmp_path / "controls.json", False)
    add_device(manager, 0)
    add_device(manager, 1)
    button = joystick_event(pygame.JOYBUTTONDOWN, 3, button=0)
    assert "p1_fire" in manager.actions_for(button, player_count=2)
    assert manager.cycle_device_slot("same:1") == "same:2"
    assert "p2_fire" in manager.actions_for(button, player_count=2)
    assert manager.event_device(button) == "same:2"
    remove_device(manager, 4)
    assert manager.cycle_device_slot("same:2") == "same:1"
    assert "p1_fire" in manager.actions_for(button, player_count=2)


def test_axis_hysteresis_and_hat_binding_are_edge_triggered(tmp_path, monkeypatch):
    monkeypatch.setattr(pygame.joystick, "Joystick", lambda _: device(3, "stick", "T.16000M"))
    manager = InputManager(tmp_path / "controls.json", False)
    add_device(manager, 0)
    slot = "stick:1"
    manager.change_deadzone(slot, 0.1)

    def axis(value):
        return joystick_event(pygame.JOYAXISMOTION, 3, axis=3, value=value)

    def hat(value):
        return joystick_event(pygame.JOYHATMOTION, 3, hat=1, value=value)

    assert not manager.bind_event("p1_left", axis(-0.65), device=slot, save=False)
    assert manager.bind_event("p1_left", axis(-0.9), device=slot, save=False)
    assert not manager.bind_event("p1_right", axis(0.9), device=slot, save=False)
    assert manager.actions_for(axis(0.0), player_count=1) == set()
    assert manager.bind_event("p1_right", axis(0.9), device=slot, save=False)
    assert manager.actions_for(axis(0.68), player_count=1) == set()
    assert manager.actions_for(axis(0.9), player_count=1) == set()
    assert manager.actions_for(axis(0.0), player_count=1) == set()
    assert manager.actions_for(axis(0.9), player_count=1) == {"p1_right"}
    assert manager.bind_event("p1_up", hat((0, 1)), device=slot, save=False)
    assert manager.actions_for(hat((0, 1)), player_count=1) == set()
    assert manager.actions_for(hat((0, 0)), player_count=1) == set()
    assert manager.actions_for(hat((0, 1)), player_count=1) == {"p1_up"}
    assert manager.label("p1_left", slot) == "Achse 4 −"


def test_controls_capture_esc_and_reserved_keys_do_not_leave_menu(tmp_path):
    pygame.init()
    manager = InputManager(tmp_path / "controls.json", False)
    states = []
    menu = ControlsMenu(SimpleNamespace(input=manager, set_state=states.append))
    menu.handle_event(key(pygame.K_RETURN))
    assert menu.waiting_for_binding
    menu.handle_event(key(pygame.K_F2))
    assert menu.waiting_for_binding
    menu.handle_event(key(pygame.K_ESCAPE))
    assert not menu.waiting_for_binding
    assert manager.bindings["p1_up"]["key"] == pygame.K_w
    assert not states

    menu.handle_event(key(pygame.K_RETURN))
    menu.handle_event(key(pygame.K_r))
    assert manager.bindings["p1_up"]["key"] == pygame.K_r
    assert not manager.config_path.exists()
    menu.handle_event(key(pygame.K_s))
    assert InputManager(manager.config_path, False).bindings["p1_up"]["key"] == pygame.K_r
    menu.handle_event(key(pygame.K_ESCAPE))
    assert states == [GameState.INTRO]

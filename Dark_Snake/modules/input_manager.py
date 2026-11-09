"""Translate keyboard and joystick events into actions and persist bindings."""

from dataclasses import dataclass
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pygame

from modules.resources import user_data_path


DEFAULT_BINDINGS = {
    "p1_up": {"key": pygame.K_w},
    "p1_down": {"key": pygame.K_s},
    "p1_left": {"key": pygame.K_a},
    "p1_right": {"key": pygame.K_d},
    "p1_fire": {"key": pygame.K_SPACE, "button": 0},
    "p2_up": {"key": pygame.K_UP},
    "p2_down": {"key": pygame.K_DOWN},
    "p2_left": {"key": pygame.K_LEFT},
    "p2_right": {"key": pygame.K_RIGHT},
    "p2_fire": {"key": pygame.K_RETURN, "button": 0},
    "pause": {"key": pygame.K_p},
    "special_effect": {"key": None, "text": "ü"},
    "menu_accept": {"key": pygame.K_RETURN, "button": 0},
}

GAMEPAD_DIRECTIONS = {
    "up": (("axis", 1, -1), ("hat_y", 0, 1)),
    "down": (("axis", 1, 1), ("hat_y", 0, -1)),
    "left": (("axis", 0, -1), ("hat_x", 0, -1)),
    "right": (("axis", 0, 1), ("hat_x", 0, 1)),
}
JOYSTICK_EVENTS = (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION)
RESERVED_KEYS = (pygame.K_ESCAPE, pygame.K_TAB, pygame.K_F2)
ANY_DEVICE = object()
DEFAULT_DEADZONE = 0.6


@dataclass
class ConnectedDevice:
    joystick: object
    guid: str
    slot: str


class InputManager:
    def __init__(self, config_path=None, initialize_joysticks=True, load_saved=True):
        self.config_path = Path(config_path or user_data_path("controls.json"))
        self.bindings = {name: dict(value) for name, value in DEFAULT_BINDINGS.items()}
        self.profiles = {}
        self.devices = {}
        self._held = {}
        if load_saved:
            self.load()
        if initialize_joysticks:
            self.refresh_joysticks()

    def refresh_joysticks(self):
        try:
            if not pygame.joystick.get_init():
                pygame.joystick.init()
            for index in range(pygame.joystick.get_count()):
                self._connect(index)
        except pygame.error:
            pass

    def _connect(self, index):
        joystick = pygame.joystick.Joystick(index)
        joystick.init()
        instance = joystick.get_instance_id()
        if instance in self.devices:
            return
        guid = joystick.get_guid()
        occupied = {device.slot for device in self.devices.values()}
        number = 1
        while f"{guid}:{number}" in occupied:
            number += 1
        slot = f"{guid}:{number}"
        self.profiles.setdefault(slot, self._profile(joystick.get_name(), 1 if not self.devices else 2))
        self.devices[instance] = ConnectedDevice(joystick, guid, slot)

    @staticmethod
    def _profile(name, player):
        return {"name": name, "player": player, "deadzone": DEFAULT_DEADZONE, "controls": {}}

    def handle_device_event(self, event):
        if event.type == pygame.JOYDEVICEADDED:
            try:
                self._connect(event.device_index)
            except pygame.error:
                pass
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.devices.pop(event.instance_id, None)
            self._held = {key: value for key, value in self._held.items()
                          if key[0] != event.instance_id}
        else:
            return False
        return True

    @staticmethod
    def _valid_control(control):
        if not isinstance(control, (tuple, list)) or len(control) != 3:
            return False
        kind, index, sign = control
        return (type(index) is int and index >= 0 and type(sign) is int
                and ((kind == "button" and sign == 0)
                     or (kind in ("axis", "hat_x", "hat_y") and sign in (-1, 1))))

    def load(self):
        try:
            with self.config_path.open(encoding="utf-8") as file:
                saved = json.load(file)
        except (OSError, ValueError):
            return
        if not isinstance(saved, dict):
            return
        version = saved.get("version")
        if version not in (None, 2):
            return
        bindings = saved.get("bindings") if version == 2 else saved
        if isinstance(bindings, dict):
            for action, binding in bindings.items():
                if action not in self.bindings or not isinstance(binding, dict):
                    continue
                for field in ("key", "button"):
                    if field in binding and (binding[field] is None or
                                             type(binding[field]) is int and binding[field] >= 0):
                        self.bindings[action][field] = binding[field]
                if action == "special_effect" and "text" in binding:
                    self.bindings[action]["text"] = "ü" if binding["text"] == "ü" else None
        profiles = saved.get("devices", {}) if version == 2 else {}
        if not isinstance(profiles, dict):
            return
        for slot, profile in profiles.items():
            if not isinstance(profile, dict) or not isinstance(profile.get("name"), str):
                continue
            player = profile.get("player")
            if type(player) is not int or player not in (1, 2):
                continue
            loaded = self._profile(profile["name"], player)
            deadzone = profile.get("deadzone")
            if type(deadzone) in (int, float) and 0.1 <= deadzone <= 0.95:
                loaded["deadzone"] = deadzone
            controls = profile.get("controls")
            if isinstance(controls, dict):
                loaded["controls"] = {
                    action: tuple(control) if control is not None else None
                    for action, control in controls.items()
                    if action in self.bindings and (control is None or self._valid_control(control))
                }
            self.profiles[slot] = loaded

    def save(self):
        payload = {"version": 2, "bindings": self.bindings, "devices": self.profiles}
        temporary = None
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.config_path.parent,
                                    prefix=".controls-", suffix=".tmp", delete=False) as file:
                temporary = Path(file.name)
                json.dump(payload, file, ensure_ascii=False, indent=2)
                file.flush()
                os.fsync(file.fileno())
            temporary.replace(self.config_path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def reset_defaults(self, *, save=True):
        self.bindings = {name: dict(value) for name, value in DEFAULT_BINDINGS.items()}
        self.profiles = {
            device.slot: self._profile(device.joystick.get_name(), 1 if index == 0 else 2)
            for index, device in enumerate(self.devices.values())
        }
        if save:
            self.save()

    def set_player(self, slot, player):
        self.profiles[slot]["player"] = player

    def change_deadzone(self, slot, delta):
        profile = self.profiles[slot]
        profile["deadzone"] = round(max(0.1, min(0.95, profile["deadzone"] + delta)), 2)

    def cycle_device_slot(self, slot):
        """Swap profiles for two identical devices if SDL cannot identify them uniquely."""
        device = next((device for device in self.devices.values() if device.slot == slot), None)
        if device is None:
            return slot
        slots = [profile for profile in self.profiles if profile.rsplit(":", 1)[0] == device.guid]
        selected = slots[(slots.index(slot) + 1) % len(slots)]
        for other in self.devices.values():
            if other.slot == selected:
                other.slot = slot
                break
        device.slot = selected
        return selected

    def device_options(self):
        active = {device.slot: instance for instance, device in self.devices.items()}
        return {
            slot: (f"{profile['name']} · Profil {slot.rsplit(':', 1)[-1]} "
                   f"· SDL {active[slot]}" if slot in active else
                   f"{profile['name']} · Profil {slot.rsplit(':', 1)[-1]} · getrennt")
            for slot, profile in self.profiles.items()
        }

    def event_device(self, event):
        if event.type not in JOYSTICK_EVENTS:
            return None
        device = self.devices.get(getattr(event, "instance_id", None))
        return device.slot if device else None

    def _control_edges(self, event, slot):
        if event.type == pygame.JOYBUTTONDOWN:
            return (("button", event.button, 0),)
        if event.type == pygame.JOYAXISMOTION:
            deadzone = self.profiles[slot]["deadzone"] if slot else DEFAULT_DEADZONE
            value = event.value
            active = (1 if value > 0 else -1) if abs(value) >= deadzone else 0
            samples = (("axis", event.axis, active, abs(value) <= deadzone * 0.75),)
        elif event.type == pygame.JOYHATMOTION:
            samples = tuple((kind, getattr(event, "hat", 0), value, not value)
                            for kind, value in zip(("hat_x", "hat_y"), event.value))
        else:
            return ()

        source = getattr(event, "instance_id", ("legacy", getattr(event, "joy", 0)))
        edges = []
        for kind, index, sign, neutral in samples:
            key = (source, kind, index)
            if neutral:
                self._held.pop(key, None)
            elif sign and key not in self._held:
                self._held[key] = sign
                edges.append((kind, index, sign))
        return edges

    def bind_event(self, action, event, *, device=ANY_DEVICE, save=True):
        if event.type == pygame.KEYDOWN and device in (None, ANY_DEVICE):
            if event.key in RESERVED_KEYS:
                return False
            self.bindings[action]["key"] = event.key
            self.bindings[action].pop("text", None)
        elif event.type in JOYSTICK_EVENTS and device is not None:
            slot = self.event_device(event)
            if device is not ANY_DEVICE and device != slot:
                return False
            controls = self._control_edges(event, slot)
            if not controls:
                return False
            if slot is not None:
                self.profiles[slot]["controls"][action] = controls[0]
            elif not hasattr(event, "instance_id") and event.type == pygame.JOYBUTTONDOWN:
                self.bindings[action]["button"] = event.button
            else:
                return False
        else:
            return False
        if save:
            self.save()
        return True

    def remove(self, action, device=None):
        if device is None:
            self.bindings[action]["key"] = None
            self.bindings[action].pop("text", None)
        else:
            self.profiles[device]["controls"][action] = None

    def keyboard_keys(self, action, player_count):
        key = self.bindings[action].get("key")
        if action == "p1_fire" and key == pygame.K_SPACE and player_count == 1:
            return key, pygame.K_RETURN
        if action == "p2_fire" and key == pygame.K_RETURN:
            return key, pygame.K_PLUS, pygame.K_KP_PLUS
        return () if key is None else (key,)

    def device_controls(self, action, slot):
        if slot is not None and action in self.profiles[slot]["controls"]:
            control = self.profiles[slot]["controls"][action]
            return (control,) if control else ()
        direction = GAMEPAD_DIRECTIONS.get(action[3:]) if action.startswith(("p1_", "p2_")) else None
        button = self.bindings[action].get("button")
        buttons = (("button", button, 0),) if button is not None else ()
        return (direction or ()) + buttons

    @staticmethod
    def _is_action_active(action, player_count):
        return player_count != 1 or not action.startswith("p2_")

    def actions_for(self, event, player_count=None):
        if self.handle_device_event(event):
            return set()
        if event.type == pygame.KEYDOWN:
            return {action for action, binding in self.bindings.items()
                    if self._is_action_active(action, player_count)
                    and (event.key in self.keyboard_keys(action, player_count)
                         or binding.get("text") and
                         getattr(event, "unicode", "").casefold() == binding["text"])}
        if event.type not in JOYSTICK_EVENTS:
            return set()
        slot = self.event_device(event)
        if slot is None and hasattr(event, "instance_id"):
            return set()
        player = (self.profiles[slot]["player"] if slot is not None else
                  1 if getattr(event, "joy", 0) == 0 else 2)
        controls = self._control_edges(event, slot)
        return {
            action for action in self.bindings if self._is_action_active(action, player_count)
            and (not action.startswith(("p1_", "p2_")) or action.startswith(f"p{player}_"))
            and any(control in self.device_controls(action, slot) for control in controls)
        }

    def conflicts(self, action, device=None):
        if device is not None:
            controls = set(self.device_controls(action, device))
            player = self.profiles[device]["player"]
            return [other for other in self.bindings if other not in (action, "menu_accept")
                    and (not other.startswith(("p1_", "p2_")) or other.startswith(f"p{player}_"))
                    and controls.intersection(self.device_controls(other, device))]
        keys = self.keyboard_keys(action, 2)
        conflicts = [other for other in self.bindings if other not in (action, "menu_accept")
                     and set(keys).intersection(self.keyboard_keys(other, 2))]
        if not action.startswith("p2_"):
            conflicts.extend(other for other in self.bindings
                             if other not in (action, "menu_accept") and not other.startswith("p2_")
                             and other not in conflicts and set(self.keyboard_keys(action, 1))
                             .intersection(self.keyboard_keys(other, 1)))
        if set(keys).intersection(RESERVED_KEYS):
            conflicts.append("navigation")
        return conflicts

    def label(self, action, device=None):
        if device is None:
            names = {pygame.K_SPACE: "Leertaste", pygame.K_RETURN: "Enter",
                     pygame.K_PLUS: "+", pygame.K_KP_PLUS: "Num +"}
            player_count = 2 if action.startswith("p2_") else 1
            keys = [names.get(key) or pygame.key.name(key).upper()
                    for key in self.keyboard_keys(action, player_count)]
            if self.bindings[action].get("text"):
                keys.append(self.bindings[action]["text"].upper())
            if action == "p1_fire" and len(keys) > 1:
                keys[-1] += " (1P)"
            return " / ".join(keys) or "–"
        labels = []
        for kind, index, sign in self.device_controls(action, device):
            if kind == "button":
                labels.append(f"Taste {index + 1}")
            elif kind == "axis":
                labels.append(f"Achse {index + 1} {'+' if sign > 0 else '−'}")
            else:
                direction = ("Rechts" if sign > 0 else "Links") if kind == "hat_x" else (
                    "Hoch" if sign > 0 else "Runter")
                labels.append(f"D-Pad {index + 1} {direction}")
        return " / ".join(labels) or "–"

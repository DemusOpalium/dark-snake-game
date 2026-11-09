import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from modules import audio, resources
from modules.game import Game


def send_mouse(menu, event_type, pos):
    if event_type == pygame.MOUSEMOTION:
        event = pygame.event.Event(event_type, pos=pos, rel=(0, 0), buttons=(1, 0, 0))
    else:
        event = pygame.event.Event(event_type, pos=pos, button=1)
    menu.handle_event(event)


def test_audio_sliders_apply_independently_before_save(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game()
    menu = game.options_menu
    assert pygame.mixer.music.get_busy()
    music, sfx = menu.music_slider, menu.sfx_slider
    sound = audio.SOUNDS["eat"]
    initial_sfx_volume = sound.get_volume()

    def unexpected_restart(*args):
        pytest.fail("Volume control restarted the current track")

    with monkeypatch.context() as patch:
        patch.setattr(pygame.mixer.music, "load", unexpected_restart)
        patch.setattr(pygame.mixer.music, "play", unexpected_restart)
        music_point = (music.rect.x + music.rect.width // 4, music.rect.centery)
        send_mouse(menu, pygame.MOUSEBUTTONDOWN, music_point)
        assert pygame.mixer.music.get_volume() == pytest.approx(0.25, abs=1 / 128)
        assert sound.get_volume() == initial_sfx_volume
        # Releasing outside the settings panel must end the current drag.
        send_mouse(menu, pygame.MOUSEBUTTONUP, (music_point[0], 15))
        assert not music.dragging

        sfx_point = (sfx.rect.x + sfx.rect.width // 2, sfx.rect.centery)
        send_mouse(menu, pygame.MOUSEBUTTONDOWN, sfx_point)
        send_mouse(menu, pygame.MOUSEMOTION, (sfx.rect.x + sfx.rect.width // 4, sfx.rect.centery))
        assert sound.get_volume() == pytest.approx(0.25, abs=1 / 128)
        assert pygame.mixer.music.get_volume() == pytest.approx(0.25, abs=1 / 128)
        send_mouse(menu, pygame.MOUSEBUTTONUP, sfx_point)
        assert sound.get_num_channels() > 0
        assert not (tmp_path / "settings.json").exists()

        menu.save()
    restarted = Game()
    assert restarted.settings["bg_music_volume"] == music.current_val
    assert restarted.settings["sfx_volume"] == sfx.current_val
    assert pygame.mixer.music.get_volume() == pytest.approx(0.25, abs=1 / 128)
    assert audio.SOUNDS["eat"].get_volume() == pytest.approx(0.25, abs=1 / 128)


def test_selected_track_survives_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    menu = Game().options_menu
    dropdown = menu.music_dropdown
    track = "FürAndreTeil2.mp3"
    send_mouse(menu, pygame.MOUSEBUTTONDOWN, dropdown.rect.center)
    x, y = dropdown.rect.center
    send_mouse(menu, pygame.MOUSEBUTTONDOWN, (x, y + (dropdown.options.index(track) + 1) * dropdown.rect.height))
    menu.save()

    with (tmp_path / "settings.json").open(encoding="utf-8") as file:
        assert json.load(file)["music_track"] == track
    restarted = Game()
    dropdown = restarted.options_menu.music_dropdown
    assert dropdown.options[dropdown.selected_index] == track
    assert pygame.mixer.music.get_busy()


def test_legacy_audio_settings_are_clamped_and_default_track_is_restored(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    (tmp_path / "settings.json").write_text(
        json.dumps({"music_volume": 0.5, "sfx_volume": 2, "music_track": "missing.mp3"}),
        encoding="utf-8",
    )
    game = Game()
    assert game.settings["bg_music_volume"] == 0.5
    assert game.settings["sfx_volume"] == 1.0
    assert game.settings["music_track"] == audio.DEFAULT_MUSIC_TRACK
    assert pygame.mixer.music.get_volume() == 0.5
    assert audio.SOUNDS["eat"].get_volume() == 1.0


def test_initialize_audio_reuses_running_mixer(monkeypatch):
    calls = []
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: (48000, -16, 2) if calls else None)
    monkeypatch.setattr(pygame.mixer, "init", lambda **settings: calls.append(settings))
    monkeypatch.setattr(audio, "SOUNDS", {})
    monkeypatch.setattr(audio, "load_sound", lambda name: name)

    assert audio.initialize_audio()
    assert audio.initialize_audio()

    assert calls == [{"frequency": 48000, "size": -16, "channels": 2, "buffer": 1024, "allowedchanges": 0}]
    assert audio.SOUNDS["eat"] == "eat.wav"
    assert audio.SOUNDS["gegner"] == "gegner.wav"

import math
import os
import pygame
from modules.crash_reporting import record_event
from modules.resources import find_asset, find_asset_directory

DEFAULT_MUSIC_TRACK = "DarkSnakeMusicIndi2.mp3"
DEFAULT_MUSIC_VOLUME = 0.3
DEFAULT_SFX_VOLUME = 1.0

_SOUND_FILES = {
    "eat": "eat.wav",
    "powerup": "powerup.wav",
    "boss": "boss.wav",
    "gameover": "gameover.wav",
    "dice": "dice.wav",
    "damage": "gameover.wav",
    "gegner": "gegner.wav",
}
SOUNDS = {}


def normalize_volume(volume, default):
    """Keep persisted and preview volumes in the mixer's supported range."""
    try:
        volume = float(volume)
    except (TypeError, ValueError, OverflowError):
        return default
    return max(0.0, min(1.0, volume)) if math.isfinite(volume) else default


def load_sound(filename):
    try:
        return pygame.mixer.Sound(str(find_asset("sounds", filename)))
    except (OSError, pygame.error) as exc:
        record_event(f"Sound {filename} konnte nicht geladen werden: {exc}")
        return None


def initialize_audio():
    """Initialize the mixer once and load effects only after audio is ready."""
    if not pygame.mixer.get_init():
        SOUNDS.clear()
        try:
            # The music library is 48 kHz stereo. 1024 samples give the
            # device more scheduling headroom than Pygame's 512 default.
            pygame.mixer.init(frequency=48000, size=-16, channels=2, buffer=1024, allowedchanges=0)
        except pygame.error as exc:
            record_event(f"Audio deaktiviert: {exc}")
            return False
    if not SOUNDS:
        SOUNDS.update((name, load_sound(filename)) for name, filename in _SOUND_FILES.items())
    return True


# Funktionen für Hintergrundmusik
def play_background_music(filename, volume=DEFAULT_MUSIC_VOLUME, loop=-1):
    """Lädt und spielt die angegebene Musikdatei aus dem Musikordner."""
    if not pygame.mixer.get_init():
        return False
    music_path = filename if os.path.isabs(filename) else str(find_asset("sounds", "music", filename))
    try:
        pygame.mixer.music.load(music_path)
        set_music_volume(volume)
        pygame.mixer.music.play(loop)
    except (OSError, pygame.error) as exc:
        record_event(f"Musik {filename} konnte nicht geladen werden: {exc}")
        return False
    return True

def stop_background_music():
    """Stoppt die aktuell laufende Hintergrundmusik."""
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()

def set_music_volume(volume):
    """Stellt die Lautstärke der Hintergrundmusik ein."""
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(normalize_volume(volume, DEFAULT_MUSIC_VOLUME))


def set_sound_volume(volume):
    if not pygame.mixer.get_init():
        return
    volume = normalize_volume(volume, DEFAULT_SFX_VOLUME)
    for sound in SOUNDS.values():
        if sound is not None:
            sound.set_volume(volume)

def get_music_library():
    """Liest alle Musikdateien aus dem Musikordner und gibt diese als Liste zurück."""
    music_dir = find_asset_directory("sounds", "music")
    try:
        return sorted(path.name for path in music_dir.iterdir()
                      if path.is_file() and path.suffix.lower() in (".mp3", ".ogg", ".wav"))
    except OSError as exc:
        record_event(f"Musikordner konnte nicht geöffnet werden: {exc}")
        return []

import os
import pygame

def load_sound(filename):
    path = os.path.join("assets", "sounds", filename)
    try:
        return pygame.mixer.Sound(path)
    except Exception as e:
        print(f"Sound {filename} konnte nicht geladen werden: {e}")
        return None

SOUNDS = {
    "eat": load_sound("eat.wav"),
    "powerup": load_sound("powerup.wav"),
    "boss": load_sound("boss.wav"),
    "gameover": load_sound("gameover.wav"),
    "dice": load_sound("dice.wav"),
    "damage": load_sound("gameover.wav"),
    "portalsound": load_sound("DarkSnakeMusicIndi2.mp3")
}

# Funktionen für Hintergrundmusik
def play_background_music(filename, volume=0.5, loop=-1):
    """Lädt und spielt die angegebene Musikdatei aus dem Musikordner."""
    music_path = os.path.join("assets", "sounds", "music", filename)
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loop)
    except Exception as e:
        print(f"Musik {filename} konnte nicht geladen werden: {e}")

def stop_background_music():
    """Stoppt die aktuell laufende Hintergrundmusik."""
    pygame.mixer.music.stop()

def set_music_volume(volume):
    """Stellt die Lautstärke der Hintergrundmusik ein."""
    pygame.mixer.music.set_volume(volume)

def get_music_library():
    """Liest alle Musikdateien aus dem Musikordner und gibt diese als Liste zurück."""
    music_dir = os.path.join("assets", "sounds", "music")
    try:
        music_files = [f for f in os.listdir(music_dir) if f.lower().endswith(('.mp3', '.ogg', '.wav'))]
        return music_files
    except Exception as e:
        print(f"Fehler beim Zugriff auf den Musikordner: {e}")
        return []


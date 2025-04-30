# 📦 DEV_STRUCTURE.md – Modulübersicht

Diese Datei beschreibt die wichtigsten Module des Dark Snake Game Projekts, ihre Abhängigkeiten und Funktionsweise.

## Hauptmodule (gameplay-relevant)

- `main.py` – Einstiegspunkt
- `game.py` – Spiellogik, Boss-System, Items, StateMachine
- `graphics.py` – Zentrale Grafikverwaltung via get_image(...)
- `config.py` – Auflösung, Farben, FPS, Schriftarten
- `level_editor.py` – Tile-Editor mit Favoriten und Simulation
- `admin_panel.py` – Debug-Tool mit 9 Buttons + Hitbox-Overlay

## UI + Optionen

- `options_menu.py` – Slider, Dropdown, Designvorschau
- `customization.py` – Snake-Kopf- und Körperauswahl
- `ui.py` – Buttons, CheckBox, Dropdown, Slider
- `controls.py` – Steuerung anzeigen (1P/2P)

## Gegner & Effekte

- `enemies.py` – Standard-Gegner
- `bolbu_enemy.py` – Spezialgegner Bolbu mit Projektil
- `boss_projectiles.py` – Boss-Schüsse
- `aoe_zones.py` – AOE-Flächen (Heilung, Schaden, Debuff)
- `fire_explosion.py` – Explosion bei Feuerballtreffer
- `audio.py` – Musik, SFX

## System

- `enums.py` – GameState, Direction, ItemType

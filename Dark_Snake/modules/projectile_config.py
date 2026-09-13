"""Zentrale, rückwärtskompatible Balancewerte für Projektile.

Geschwindigkeiten der Dictionary-Projektile werden in Kacheln pro Tick angegeben;
Klassen mit einem ``pygame.Rect`` bewegen sich dagegen in Pixeln pro Tick.
Lebensdauern und Cooldowns sind Tickzahlen (das Spiel läuft mit ``FPS`` Ticks/s).
"""

PLAYER_PROJECTILE_DAMAGE = 10
PLAYER_PROJECTILE_LIFETIME_TICKS = None  # bisher nur durch den Spielfeldrand begrenzt
PLAYER_FIREBALL_SPEED_PX_PER_TICK = 6
PLAYER_FIREBALL_DAMAGE = 3
PLAYER_FIREBALL_LIFETIME_TICKS = 180
PLAYER_FIREBALL_COOLDOWN_SECONDS = 2

BOLBU_PROJECTILE_SPEED_PX_PER_TICK = 4
BOLBU_PROJECTILE_DAMAGE = 2
BOLBU_PROJECTILE_LIFETIME_TICKS = 240
BOLBU_SHOOT_COOLDOWN_SECONDS = 2.5

BOSS_PROJECTILE_SPEED_PX_PER_TICK = 2.0
BOSS_PROJECTILE_DAMAGE = 5
BOSS_PROJECTILE_LIFETIME_TICKS = 600
BOSS_FLAME_SPEED_PX_PER_TICK = 2.4
BOSS_FLAME_DAMAGE = 8
BOSS_FLAME_LIFETIME_TICKS = 1200

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Modul: game.py
# Zweck: Hauptlogik für Dark-Snake inkl. Kollisionsprüfung, Schadensberechnung,
#        Projektil‑Schusstiming, Health-System, AoE-Effekten etc.
#

import pygame, sys, random, time, os, datetime, json
from functools import lru_cache
from math import sqrt, atan2, cos, sin, pi
from pygame.math import Vector2

from modules.enums import GameState, Direction, ItemType
from config import (WINDOW_WIDTH, WINDOW_HEIGHT, GRID_SIZE, FPS, GRID_WIDTH, GRID_HEIGHT,
                    DARK_GREY, WHITE, GREEN, RED, PURPLE, ORANGE, GOLDEN, LEADERBOARD_FILE,
                    START_SPEED, MAX_SPEED, PROJECTILE_SPEED_FACTOR, AUTO_SHOOT_INTERVAL, BORDER_SIZE, UI_CONTAINER_HEIGHT)
# <-- Hier den fehlenden Import hinzufügen:
from modules.graphics import (
    load_image, load_projectile_image, scale_sprite,
    SNAKE_HEAD_IMG, SNAKE_HEAD1G20, SNAKE_HEAD2G20, SNAKE_HEAD3G20,
    SNAKE_HEAD_BETA,
    SNAKE_BODY_IMG, SNAKE_BODY_BETA, SNAKE_BODY_Body7, SNAKE_BODY_Body5,
    SNAKE_BODY_Body4, SNAKE_BODY_Body2, SNAKE_BODY_Body6,
    PROJECTILE_IMG, TITLE_IMG,
    BOSS_IMG, BOSS_ALT_IMG,
    PORTAL_IMAGES, ITEM_IMAGES,
    OPTIONS_BUTTON_IMG, PLAY_BUTTON_IMG,
)
from modules.level_editor import LevelEditor
from modules.audio import (
    DEFAULT_MUSIC_TRACK, DEFAULT_MUSIC_VOLUME, DEFAULT_SFX_VOLUME, SOUNDS,
    get_music_library, initialize_audio, normalize_volume, play_background_music,
    set_music_volume, set_sound_volume,
)
from modules.ui import Button, Slider, CheckBox, Dropdown
from modules.aoe_zones import AoEZone, DamageZone, HealZone, DebuffZone, FollowZone, GrowingBossAOEZone  # [KS_TAG: BOSS_AOE]
from modules.controls import ControlsMenu
from modules.input_manager import InputManager
from modules.resources import asset_path, custom_level_path, user_data_path
from modules.customization import CustomizationMenu
from modules.enemies import NormalEnemy
from modules.bolbu_enemy import BolbuEnemy
from modules.options_menu import OptionsMenu, ExtendedOptionsMenu
from modules.admin_panel import AdminPanel
from modules.fire_explosion import FireExplosionAnimation
from modules.crash_reporting import record_event
from modules.simulation_ui import SimulationMenu
from modules.effect_manager import EffectManager
from modules.frame_metrics import FrameMetrics
from modules.projectile_config import (
    MAX_BOSS_FLAMES, MAX_BOSS_GRID_PROJECTILES, MAX_ENEMY_PROJECTILES,
    MAX_PLAYER_GRID_PROJECTILES,
    PLAYER_FIREBALL_COOLDOWN_SECONDS, PLAYER_FIREBALL_DAMAGE,
    PLAYER_FIREBALL_LIFETIME_TICKS, PLAYER_FIREBALL_SPEED_PX_PER_TICK,
    PLAYER_PROJECTILE_DAMAGE,
)

ENEMY_LIMIT = {1: 12, 2: 16}
BOSS_BODY_DAMAGE = 10
BOSS_BODY_HIT_INTERVAL = 1.0
BOSS_SPAWN_PROTECTION = 3.0
CLASSIC_BOSS_PROJECTILE_DAMAGE = 10

DIRECTION_ACTIONS = {direction.name.lower(): direction for direction in Direction}
OPPOSITE_DIRECTION = {
    Direction.UP: Direction.DOWN, Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT, Direction.RIGHT: Direction.LEFT,
}

# Boss-Projektil-Grafiken (zufällige Auswahl)
BOSS_PROJECTILES = []
for fname in ["Projektil2.png", "Projektil3.png", "Projektil4.png", "Projektil5.png"]:
    path = asset_path("graphics", fname)
    try:
        img = pygame.image.load(path).convert_alpha()
        BOSS_PROJECTILES.append(img)
    except Exception as e:
        print(f"Fehler beim Laden von {fname}: {e}")

def get_random_projectile_color():
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))

@lru_cache(maxsize=1)
def _available_aoe_effect_paths():
    effect_folder = asset_path("graphics", "AOEEffekte")
    effect_files = [
        "AcidAOE1.png", "AcidAOE2.png", "AcidAOE3.png", "AcidAOE4.png",
        "AcidBlop1.png", "AcidBlop2.png", "AcidBlop3.png", "AcidBlop4.png",
        "DarkAOE1.png", "DarkAOE2.png", "DarkAOE3.png", "DarkAOE4.png",
        "DarkBlob1.png", "DarkBlop2.png", "DarkBlop3.png",
        "DungeonAOE.png", "DungeonAOE2.png", "DungeonAOE3.png", "DungeonAOE4.png",
        "FigurAOE1.png", "FigurAOE2.png", "FigurAOE3.png",
        "FireAOE1.png", "FireAOE2.png", "FireAOE3.png", "FireAOE4.png",
        "Fire-FeuerHoch.png", "Fire-FireHoch2.png",
        "GhostAOE1.png", "GhostAOE2.png", "GhostAOE3.png", "GhostAOE4.png",
        "GhostAOE6.png", "GhostAOE7.png", "GhostAOE8.png", "GhostAOE9.png",
        "GohstAOE5.png",
        "HolyAOE1.png", "HolyAOE2.png", "HolyAOE3.png",
        "IceAOE1.png",
        "LightAOE.png", "LightAOE2.png", "LightAOE3.png",
        "MagicAOE1.png", "MagicAOE2.png",
        "MetallAOE1.png",
        "ParadoxAOE1.png",
        "WaterAOE1.png", "WaterAOE2.png",
        "WindAOE1.png", "WindAOE2.png"
    ]
    return tuple(path for fname in effect_files
                 if os.path.isfile(path := os.path.join(effect_folder, fname)))


@lru_cache(maxsize=64)
def _load_aoe_effect(path, grid_size):
    image = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(image, (grid_size * 3, grid_size * 3))


def get_aoe_effect():
    candidates = list(_available_aoe_effect_paths())
    while candidates:
        path = random.choice(candidates)
        try:
            return _load_aoe_effect(path, GRID_SIZE)
        except (OSError, pygame.error):
            candidates.remove(path)
    return None

# === Boss-Klassen ===
class Boss:
    def __init__(self, level, health_multiplier=1.0):
        self.x = random.randint(5, GRID_WIDTH - 5)
        self.y = random.randint(5, GRID_HEIGHT - 5)
        self.size = 3 + level // 2
        base_health = max(30, 3 + level * 5)
        self.health = int(base_health * health_multiplier)
        self.speed = 1 + level * 0.2 + random.uniform(0, 0.5)
        self.last_move = time.time()
        self.chase_speed = 0.5
        self.attack_mode = "normal"
        self.spawn_time = time.time()  # Zeitpunkt des Spawns
        boss_files = ["Boss-AlexG60.png", "Boss-BolgiG60.png", "Boss-DemusG60.png",
                      "Boss-FinG60.png", "Boss-GlobyG60.png", "Boss-NeoG60.png",
                      "Boss-RingG60.png", "Boss-SkullPurPurG60.png"]
        self.image = None
        fname = random.choice(boss_files)
        if fname == "Boss-DemusG60.png":
            self.frames = []
            self.current_frame = 0
            self.last_frame_time = time.time()
            folder = asset_path("graphics", "Boss001")
            for i in range(49):
                frame_filename = os.path.join(folder, f"frame{i:04d}.png")
                try:
                    img = pygame.image.load(frame_filename).convert_alpha()
                    img = pygame.transform.scale(img, (int(60 * (GRID_SIZE/20)), int(60 * (GRID_SIZE/20))))
                    self.frames.append(img)
                except Exception as e:
                    print(f"Fehler beim Laden von {frame_filename}: {e}")
            if self.frames:
                self.image = self.frames[0]
        elif fname == "Boss-RingG60.png":
            self.frames = []
            self.current_frame = 0
            self.last_frame_time = time.time()
            folder = asset_path("graphics", "Boss002")
            for i in range(15):
                frame_filename = os.path.join(folder, f"frame{i:04d}.png")
                try:
                    img = pygame.image.load(frame_filename).convert_alpha()
                    img = pygame.transform.scale(img, (int(60 * (GRID_SIZE/20)), int(60 * (GRID_SIZE/20))))
                    self.frames.append(img)
                except Exception as e:
                    print(f"Fehler beim Laden von {frame_filename}: {e}")
            if self.frames:
                self.image = self.frames[0]
        elif fname == "Boss-FinG60.png":
            self.frames = []
            self.current_frame = 0
            self.last_frame_time = time.time()
            folder = asset_path("graphics", "Boss003")
            for i in range(15):
                frame_filename = os.path.join(folder, f"frame{i:04d}.png")
                try:
                    img = pygame.image.load(frame_filename).convert_alpha()
                    img = pygame.transform.scale(img, (int(60 * (GRID_SIZE/20)), int(60 * (GRID_SIZE/20))))
                    self.frames.append(img)
                except Exception as e:
                    print(f"Fehler beim Laden von {frame_filename}: {e}")
            if self.frames:
                self.image = self.frames[0]
        else:
            path = asset_path("graphics", fname)
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.scale(img, (self.size * GRID_SIZE, self.size * GRID_SIZE))
            except Exception as e:
                print(f"Fehler beim Laden von Bossgrafik {fname}: {e}")
        if SOUNDS.get("boss"):
            SOUNDS["boss"].play()
        self.special_attack_timer = time.time() + random.randint(5, 10)
        self.next_aoe = time.time() + 5
        self.next_proj = time.time() + 3
        self.aoe_effect = None
        self.announcement = "Boss Down Easy Going !!"

    def update(self, current_time):
        if current_time - self.last_move >= self.chase_speed:
            self.last_move = current_time
            self.x += random.choice([-1, 0, 1])
            self.y += random.choice([-1, 0, 1])
            self.x = max(0, min(self.x, GRID_WIDTH - self.size))
            self.y = max(0, min(self.y, GRID_HEIGHT - self.size))
        if hasattr(self, 'frames') and self.frames:
            self.update_animation(current_time)
        if current_time >= self.next_aoe:
            self.next_aoe = current_time + 5
            self.aoe_effect = {
                "image": get_aoe_effect(),
                "start_time": current_time,
                "duration": 7,
                "max_size": self.size * GRID_SIZE * 3
            }
            # Schaden erst nach 3 Sekunden Spawn-Zeit
            if current_time - self.spawn_time >= 3:
                return "aoe"
        if current_time >= self.next_proj:
            self.next_proj = current_time + 3
            if current_time - self.spawn_time >= 3:
                return "boss_shoot"
        return None

    def update_animation(self, current_time):
        if current_time - self.last_frame_time > 0.1:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.last_frame_time = current_time

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.x * GRID_SIZE, self.y * GRID_SIZE))
        else:
            pygame.draw.rect(screen, RED, (self.x * GRID_SIZE, self.y * GRID_SIZE,
                                           self.size * GRID_SIZE, self.size * GRID_SIZE))
        bar_width = self.size * GRID_SIZE
        bar_height = 5
        life_ratio = self.health / max(30, 3 + self.health)
        life_bar = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE - 10,
                               int(bar_width * life_ratio), bar_height)
        pygame.draw.rect(screen, GREEN, life_bar)
        pygame.draw.rect(screen, WHITE, (self.x * GRID_SIZE, self.y * GRID_SIZE - 10,
                                         bar_width, bar_height), 1)

    def draw_aoe(self, screen):
        effect = self.aoe_effect
        if effect is None:
            return
        elapsed = time.time() - effect["start_time"]
        if elapsed >= effect["duration"]:
            self.aoe_effect = None
            return
        image = effect["image"]
        if image is None:
            return
        side = self.size * GRID_SIZE
        scale = 1 + elapsed * ((effect["max_size"] / side - 1) / effect["duration"])
        diameter = int(side * scale)
        aoe_img = pygame.transform.scale(image, (diameter, diameter))
        aoe_img.set_alpha(204)
        offset = (side - diameter) // 2
        screen.blit(aoe_img, (self.x * GRID_SIZE + offset, self.y * GRID_SIZE + offset))

    def get_render_rect(self):
        rect = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE,
                           self.size * GRID_SIZE, self.size * GRID_SIZE)
        return rect

    def get_hitbox(self):
        """Bosses intentionally retain their generous gameplay rectangle."""
        return self.get_render_rect()

    def get_rect(self):
        return self.get_hitbox()

    def take_damage(self):
        self.health -= 1
        if SOUNDS.get("powerup"):
            SOUNDS["powerup"].play()
        return self.health <= 0

class Boss2(Boss):
    def __init__(self, level, health_multiplier=1.0):
        super().__init__(level, health_multiplier)
        self.size = 4 + level // 2
        base_health = max(30, 5 + level * 5)
        self.health = int(base_health * health_multiplier)
        self.speed = 1 + level * 0.25 + random.uniform(0, 0.5)
        self.chase_speed = 0.4
        self.attack_mode = "shield"
        self.spawn_time = time.time()
        boss_files = ["Boss-AlexG60.png", "Boss-BolgiG60.png", "Boss-DemusG60.png",
                      "Boss-FinG60.png", "Boss-GlobyG60.png", "Boss-NeoG60.png",
                      "Boss-RingG60.png", "Boss-SkullPurPurG60.png"]
        self.image = None
        if boss_files:
            fname = random.choice(boss_files)
            path = asset_path("graphics", fname)
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.scale(img, (self.size * GRID_SIZE, self.size * GRID_SIZE))
            except Exception as e:
                print(f"Fehler beim Laden von Bossgrafik {fname}: {e}")
        self.special_attack_timer = time.time() + random.randint(5, 10)
        self.next_aoe = time.time() + 6
        self.next_proj = time.time() + 4
        self.announcement = "Boss2 Down Easy Going !!"

# === Portal-Klasse ===
class Portal:
    def __init__(self):
        self.x = random.randint(0, GRID_WIDTH - 1)
        self.y = random.randint(0, GRID_HEIGHT - 1)
        self.image = random.choice(PORTAL_IMAGES)
        self.event = random.choice(["teleport", "boss", "loot", "color_change", "dice_event"])
        self.duration = 60
        self.start_time = time.time()
        self.width, self.height = 40, 40

    def draw(self, screen):
        if self.image:
            img = pygame.transform.scale(self.image, (self.width, self.height))
            screen.blit(img, (self.x * GRID_SIZE, self.y * GRID_SIZE))
        else:
            pygame.draw.rect(screen, ORANGE, (self.x * GRID_SIZE, self.y * GRID_SIZE, self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, self.width, self.height)

# === Item-Klasse ===
class Item:
    def __init__(self, item_type, hitbox_scale=0.85, hitbox_offset=(0, 0)):
        self.x = random.randint(0, GRID_WIDTH - 1)
        self.y = random.randint(0, GRID_HEIGHT - 1)
        self.type = item_type
        self.activation_time = 0
        self.duration = 0
        self.hitbox_scale = hitbox_scale
        self.hitbox_offset = hitbox_offset

    def get_render_rect(self):
        img = ITEM_IMAGES.get(self.type.name)
        size = img.get_size() if img else (GRID_SIZE, GRID_SIZE)
        return pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, *size)

    def get_hitbox(self):
        render = self.get_render_rect()
        width = max(1, round(render.width * self.hitbox_scale))
        height = max(1, round(render.height * self.hitbox_scale))
        rect = pygame.Rect(0, 0, width, height)
        rect.center = render.center
        rect.move_ip(*self.hitbox_offset)
        return rect

    def draw(self, screen):
        key = self.type.name
        img = ITEM_IMAGES.get(key, None)
        if img:
            screen.blit(img, (self.x * GRID_SIZE, self.y * GRID_SIZE))
        else:
            if self.type == ItemType.SPECIAL_DAMAGE:
                pygame.draw.circle(screen, PURPLE, (self.x * GRID_SIZE + GRID_SIZE // 2,
                                                     self.y * GRID_SIZE + GRID_SIZE // 2), GRID_SIZE // 2)
            elif self.type == ItemType.PROJECTILE_SHOOT:
                pygame.draw.circle(screen, (0, 255, 255), (self.x * GRID_SIZE + GRID_SIZE // 2,
                                                            self.y * GRID_SIZE + GRID_SIZE // 2), GRID_SIZE // 2)
            else:
                pygame.draw.circle(screen, RED, (self.x * GRID_SIZE + GRID_SIZE // 2,
                                                  self.y * GRID_SIZE + GRID_SIZE // 2), GRID_SIZE // 2)

# === Achievement-Manager ===
class AchievementManager:
    def __init__(self, game):
        self.game = game

    def draw_achievements(self, surface):
        y_offset = 90
        for achievement in self.game.achievement_messages[:]:
            message, expire_time = achievement
            if time.time() > expire_time:
                self.game.achievement_messages.remove(achievement)
            else:
                txt = pygame.font.SysFont('Arial', 20).render(message, True, ORANGE)
                surface.blit(txt, (20, y_offset))
                y_offset += 25

    def draw_portal_event(self, surface):
        if self.game.portal_effect_active and self.game.portal_effect_type:
            txt = pygame.font.SysFont('Arial', 24, bold=True).render("Portal: " + str(self.game.portal_effect_type), True, PURPLE)
            surface.blit(txt, (WINDOW_WIDTH - txt.get_width() - 20, 60))
        # === Health-Bar-Funktion für 2-Spieler-Modus ===

def draw_health_bar_two(game):
    # Spieler 1 Health-Bar (links)
    bar_width = 200
    bar_height = 20
    x1 = 20
    y = 80
    health_percent1 = max(0, min(1.0, game.player_health_p1 / 100.0))
    if health_percent1 > 0.5:
        red1 = int((1 - health_percent1) * 2 * 255)
        green1 = 255
    else:
        red1 = 255
        green1 = int(health_percent1 * 2 * 255)
    color1 = (red1, green1, 0)
    pygame.draw.rect(game.screen, DARK_GREY, (x1, y, bar_width, bar_height))
    pygame.draw.rect(game.screen, color1, (x1, y, int(bar_width * health_percent1), bar_height))
    pygame.draw.rect(game.screen, WHITE, (x1, y, bar_width, bar_height), 2)
    # Spieler 2 Health-Bar (rechts)
    x2 = WINDOW_WIDTH - bar_width - 20
    health_percent2 = max(0, min(1.0, game.player_health_p2 / 100.0))
    color2 = (0, 128, 255)
    pygame.draw.rect(game.screen, DARK_GREY, (x2, y, bar_width, bar_height))
    pygame.draw.rect(game.screen, color2, (x2, y, int(bar_width * health_percent2), bar_height))
    pygame.draw.rect(game.screen, WHITE, (x2, y, bar_width, bar_height), 2)

            # === Hauptklasse Game (Finale Version mit Respawn-Unbesiegbarkeit und verbesserter Kollisionsprüfung) ===
class Game:
    def __init__(self, headless=False):
        global WINDOW_WIDTH, WINDOW_HEIGHT, GRID_WIDTH, GRID_HEIGHT
        self.headless = headless
        if headless:
            # Gameplay code deliberately continues to execute while simulating and
            # some of it renders status information during update().  A plain
            # Surface provides the same drawing target without creating an OS
            # window (unlike pygame.display.set_mode()).
            self.screen = pygame.Surface(
                (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA
            )
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            pygame.display.set_caption("Dark-Snake")
            try:
                icon = pygame.image.load(asset_path("graphics", "titel2.png")).convert_alpha()
                icon = pygame.transform.scale(icon, (32, 32))
                pygame.display.set_icon(icon)
            except Exception as e:
                print(f"Fehler beim Laden des Icons: {e}")
        self.clock = pygame.time.Clock()
        self.metrics = FrameMetrics()
        self.effect_manager = EffectManager()
        self._effect_update_time = time.monotonic()
        self.settings = {
            'initial_speed': START_SPEED,
            'fullscreen': False,
            'sfx_volume': DEFAULT_SFX_VOLUME,
            'bg_music_volume': DEFAULT_MUSIC_VOLUME,
            'music_track': DEFAULT_MUSIC_TRACK,
            'difficulty': 1.0,
            'field_scale': 1.0,
            'snake_design': 0,
            'custom_head_p1': None,
            'custom_body_p1': None,
            'custom_head_p2': None,
            'custom_body_p2': None,
            'projectile_speed_factor': PROJECTILE_SPEED_FACTOR,
            'auto_shoot_interval': AUTO_SHOOT_INTERVAL,  # Neuer konfigurierbarer Parameter für die Schussfrequenz
            'enemy_spawn_rate': 0.002,
            'boss_health_multiplier': 1.0
        }
        self.load_settings()
        self.music_tracks = get_music_library()
        if self.settings['music_track'] not in self.music_tracks:
            self.settings['music_track'] = (DEFAULT_MUSIC_TRACK if DEFAULT_MUSIC_TRACK in self.music_tracks
                                            else next(iter(self.music_tracks), None))
        if not headless and initialize_audio():
            set_sound_volume(self.settings['sfx_volume'])
            track = self.settings['music_track']
            volume = self.settings['bg_music_volume']
            if track and not play_background_music(track, volume):
                if track != DEFAULT_MUSIC_TRACK and DEFAULT_MUSIC_TRACK in self.music_tracks:
                    if play_background_music(DEFAULT_MUSIC_TRACK, volume):
                        self.settings['music_track'] = DEFAULT_MUSIC_TRACK
        self.player_count = 1
        self.input = InputManager(initialize_joysticks=not headless, load_saved=not headless)
        self.intro_focus = 0
        self.create_ui_elements()
        self.reset_game()
        self.current_frame_index = 0
        self.last_anim_time = time.time()
        self.last_auto_shoot = time.time()
        self.last_auto_shoot1 = time.time()
        self.last_auto_shoot2 = time.time()
        self.default_background_surface = (pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                                           if headless else self._build_default_background())
        self.level_background_surface = self.default_background_surface.copy()
        self.background = self.level_background_surface
        self.menu_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        if not headless:
            self.menu_bg.fill(DARK_GREY)
        self.intro_bg = self.menu_bg.copy()
        self.last_click_time = 0
        self.double_click_interval = 0.5
        self.respawn_invincible_until = 0
        self.last_head_pos = None
        self.still_timer = None

        # Health-Variablen
        self.player_health = 100  
        self.player_health_p1 = 100
        self.player_health_p2 = 100

        self.effects = {k: 0 for k in ('speed_boost','speed_reduction','score_boost',
                                       'invincibility','length_shortener','length_double','projectile_shoot')}
        self.dice_result = None
        self.dice_display_until = 0
        self.leaderboard_mode = False
        self.name_input = ""
        self.leaderboard = self.load_leaderboard()
        self.special_level_timer = time.time() + 120
        self.boss_spawn_timer = time.time() + 60
        self.last_boss_effect_time = 0
        self.boss_effect_cooldown = 30
        self.portal = None
        self.portal_spawn_cooldown = time.time() + 30
        self.portal_effect_active = False
        self.portal_effect_end = 0
        self.portal_effect_type = None
        self.projectiles = []
        self.boss_flame_projectiles = []  # [KS_TAG: BOSS_FLAME_LIST]
        self.enemy_projectiles = []
        # FlameProjectile-System initialisieren
        self.flame_projectiles = []
        self.explosions = []  # reset explosions list
        self.explosions = []  # list of active explosion animations
        self.fireball_cooldown = 0
        self.fireball_cooldown_p1 = 0
        self.fireball_cooldown_p2 = 0
        self.achievement_messages = []
        self.enemies = []
        self.controls_menu = ControlsMenu(self)
        self.custom_menu = None
        self.options_menu = ExtendedOptionsMenu(self)
        self.game_state = GameState.INTRO
        self.next_direction = Direction.RIGHT
        self.snake_direction = Direction.RIGHT
        self.extra_auto_shots = 0
        self.aoe_zones = []
        self.create_additional_ui()
        self.achievement_manager = AchievementManager(self)
        # Respawn-Unbesiegbarkeit: 3 Sekunden direkt nach dem Spawn
        self.boss_fight_active = False  # [KS_TAG: ADMIN_BOSS_INIT]
        self.boss = None
        self.admin_panel = AdminPanel(self)
        self.debug_show_hitboxes = False  # [KS_TAG: DEBUG_HITBOX]
        self.combat_events = []
        self.respawn_invincible_until = 0
        self.level_editor = LevelEditor(self)
        self.simulation_menu = SimulationMenu(self)
        # Construction calls reset_game before all display resources exist.  Ensure
        # the initial menu has no pre-created round after initialization as well.
        self.clear_game_state()

    def create_ui_elements(self):
        center_x = WINDOW_WIDTH // 2
        button_width = 160
        button_height = 40
        def scale_image(img):
            if img:
                w, h = img.get_size()
                return pygame.transform.scale(img, (int(w * 0.6), int(h * 0.6)))
            return None
        self.intro_buttons = [
            Button(center_x - 100, WINDOW_HEIGHT - 500, button_width, button_height, "Spieler 1",
                   action=lambda: self.start_game(1), image=scale_image(OPTIONS_BUTTON_IMG)),
            Button(center_x - 100, WINDOW_HEIGHT - 440, button_width, button_height, "Spieler 2",
                   action=lambda: self.start_game(2), image=scale_image(OPTIONS_BUTTON_IMG)),
            Button(center_x - 100, WINDOW_HEIGHT - 380, button_width, button_height, "Optionen",
                   action=lambda: self.set_state(GameState.SETTINGS), image=scale_image(PLAY_BUTTON_IMG)),
            Button(center_x - 100, WINDOW_HEIGHT - 320, button_width, button_height, "Steuerung",
                   action=lambda: self.set_state(GameState.CONTROLS), image=scale_image(PLAY_BUTTON_IMG)),
            Button(center_x - 100, WINDOW_HEIGHT - 260, button_width, button_height, "Besten-Liste",
                   action=lambda: self.set_state(GameState.LEADERBOARD), image=scale_image(PLAY_BUTTON_IMG)),
            Button(center_x - 100, WINDOW_HEIGHT - 200, button_width, button_height, "Beenden",
                   color=RED, action=lambda: sys.exit(), image=scale_image(PLAY_BUTTON_IMG)),
            Button(center_x - 100, WINDOW_HEIGHT - 140, button_width, button_height, "Entwickler",
                   action=lambda: self.set_state(GameState.SIMULATION), image=scale_image(PLAY_BUTTON_IMG))
        ]

    def create_additional_ui(self):
        center_x = WINDOW_WIDTH // 2
        button_width = 160
        button_height = 40
        self.pause_buttons = [
            Button(center_x - 100, WINDOW_HEIGHT // 2, button_width, button_height, "WEITER",
                   action=self._resume_game),
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 80, button_width, button_height, "HAUPTMENÜ",
                   color=PURPLE, action=lambda: self.confirm_back_to_main()),
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 160, button_width, button_height, "BEENDEN",
                   color=RED, action=lambda: sys.exit())
        ]
        self.game_over_buttons = [
            Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 100, button_width, button_height, "NEUSTART",
                   action=lambda: self.start_game(self.player_count)),
            Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 180, button_width, button_height, "HAUPTMENÜ",
                   color=PURPLE, action=lambda: self.confirm_back_to_main())
        ]

    def load_leaderboard(self):
        leaderboard = []
        path = user_data_path(LEADERBOARD_FILE)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    try:
                        name, score = line.strip().split(',')
                        leaderboard.append((name, int(score)))
                    except:
                        pass
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        return leaderboard

    def intro_state(self):
        return GameState.INTRO

    def open_customization(self):
        self.set_state(GameState.CUSTOMIZATION)
        self.custom_menu = CustomizationMenu(self)

    def load_settings(self):
        if self.headless:
            return
        try:
            with open(user_data_path("settings.json"), encoding="utf-8") as file:
                saved = json.load(file)
            if isinstance(saved, dict):
                for key in self.settings:
                    if key in saved:
                        self.settings[key] = saved[key]
                music_volume = saved.get('bg_music_volume', saved.get('music_volume'))
                self.settings['bg_music_volume'] = normalize_volume(music_volume, DEFAULT_MUSIC_VOLUME)
                self.settings['sfx_volume'] = normalize_volume(self.settings['sfx_volume'], DEFAULT_SFX_VOLUME)
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            record_event(f"Einstellungen konnten nicht geladen werden: {exc}")

    def save_settings(self):
        try:
            with open(user_data_path("settings.json"), "w", encoding="utf-8") as file:
                json.dump(self.settings, file, ensure_ascii=False, indent=2)
        except OSError as exc:
            self.add_achievement("Einstellungen konnten nicht gespeichert werden")
            record_event(f"Einstellungen konnten nicht gespeichert werden: {exc}")
        set_music_volume(self.settings['bg_music_volume'])
        set_sound_volume(self.settings['sfx_volume'])

    def start_game(self, players):
        self.player_count = players
        self.reset_game()
        if players == 2:
            self.snake1 = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
            self.snake2 = [(GRID_WIDTH // 2, GRID_HEIGHT // 2 + 2)]
        else:
            self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self._reset_snake_interpolation()
        self.spawn_food()
        level_path = custom_level_path() if not self.headless else None
        if level_path and os.path.exists(level_path):
            try:
                self.level_map = self.level_editor.read_map()
                self.build_background_from_map()
                self.background = self.level_background_surface
                print("[INFO] Benutzerdefinierte Map als Hintergrund geladen.")
            except Exception as e:
                print(f"[WARN] Level konnte nicht geladen werden: {e}")
        else:
            print("[INFO] Kein Editor-Level vorhanden. Standardhintergrund wird verwendet.")

        self.set_state(GameState.GAME)

    def confirm_back_to_main(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        msg = pygame.font.SysFont('Comic Sans MS', 30).render("Zum Hauptmenü?", True, WHITE)
        self.screen.blit(msg, (WINDOW_WIDTH // 2 - msg.get_width() // 2, WINDOW_HEIGHT // 2 - msg.get_height() // 2))
        self.admin_panel.draw(self.screen)
        pygame.display.update()
        time.sleep(2)
        self.set_state(self.intro_state())

    def set_state(self, state):
        previous = getattr(self, "game_state", None)
        if state == GameState.INTRO and previous != GameState.INTRO:
            self.clear_game_state()
        if state == GameState.PAUSE and previous in (GameState.GAME, GameState.BOSS_FIGHT):
            self._paused_state = previous
            self.metrics.cancel_pending()
        self.game_state = state
        if state == GameState.GAME or (previous == GameState.PAUSE and state == GameState.BOSS_FIGHT):
            self.last_update_time = time.time()

    def _resume_game(self):
        self.set_state(getattr(self, "_paused_state", GameState.GAME))

    def reset_game(self):
        self.metrics.cancel_pending()
        if hasattr(self, "effect_manager"):
            self.effect_manager.clear()
        self.leaderboard_mode = False
        self.name_input = ""
        self.game_state = self.intro_state()
        # Never retain inactive player objects or transient combat state.
        self.snake = []
        self.snake1 = []
        self.snake2 = []
        self.previous_snake = []
        self.previous_snake1 = []
        self.previous_snake2 = []
        # Respawn-Unbesiegbarkeit setzen: 3 Sekunden nach Reset
        self.respawn_invincible_until = time.time() + 3
        if self.player_count == 2:
            self.snake_direction1 = Direction.RIGHT
            self.snake_direction2 = Direction.RIGHT
            self.next_direction1 = Direction.RIGHT
            self.next_direction2 = Direction.RIGHT
            self.last_auto_shoot1 = time.time()
            self.last_auto_shoot2 = time.time()
            self.player_health_p1 = 100
            self.player_health_p2 = 100
        else:
            self.snake_direction = Direction.RIGHT
            self.next_direction = Direction.RIGHT
            self.last_auto_shoot = time.time()
            self.player_health = 100
        self.items = []
        self.score = 0
        self.level = 1
        self.experience = 0
        self.exp_to_next_level = 100
        self.speed = self.settings['initial_speed']
        self.last_update_time = time.time()
        self.effects = {k: 0 for k in ('speed_boost', 'speed_reduction', 'score_boost',
                                       'invincibility', 'length_shortener', 'length_double', 'projectile_shoot')}
        self.boss = None
        self.boss_fight_active = False
        self._boss_contact_ready_at = {}
        self.boss_spawn_timer = time.time() + 60
        self.game_over_time = 0
        self.pause_time = 0
        self.lives = 3
        self.dice_result = None
        self.dice_display_until = 0
        self.last_boss_effect_time = 0
        self.portal = None
        self.portal_effect_active = False
        self.portal_effect_end = 0
        self.portal_effect_type = None
        self.portal_spawn_cooldown = time.time() + 30
        self.projectiles = []
        self.boss_flame_projectiles = []  # [KS_TAG: BOSS_FLAME_LIST]
        self.enemy_projectiles = []
        # FlameProjectile-System initialisieren
        self.flame_projectiles = []
        self.fireball_cooldown = 0
        self.fireball_cooldown_p1 = 0
        self.fireball_cooldown_p2 = 0
        self.achievement_messages = []
        self.enemies = []
        self.last_auto_shoot = time.time()
        self.extra_auto_shots = 0
        self.aoe_zones = []

    def clear_game_state(self):
        self.metrics.cancel_pending()
        """Drop every object belonging to a round before showing a menu."""
        self.snake = []
        self.snake1 = []
        self.snake2 = []
        self.previous_snake = []
        self.previous_snake1 = []
        self.previous_snake2 = []
        self.items = []
        self.enemies = []
        self.aoe_zones = []
        self.projectiles = []
        self.flame_projectiles = []
        self.boss_flame_projectiles = []
        self.enemy_projectiles = []
        self.explosions = []
        self.effect_manager.clear()
        self.portal = None
        self.portal_effect_active = False
        self.portal_effect_type = None
        self.boss = None
        self.boss_fight_active = False
        self.lives = 0
        self.player_health = self.player_health_p1 = self.player_health_p2 = 0
        if hasattr(self, "default_background_surface"):
            self.level_background_surface = self.default_background_surface.copy()
            self.background = self.level_background_surface

    def _reset_snake_interpolation(self):
        self.metrics.cancel_pending()
        """Synchronize visual history without changing logical grid state."""
        self.previous_snake = list(self.snake)
        self.previous_snake1 = list(self.snake1)
        self.previous_snake2 = list(self.snake2)

    def _capture_previous_snakes(self):
        self.previous_snake = list(self.snake)
        self.previous_snake1 = list(self.snake1)
        self.previous_snake2 = list(self.snake2)

    def snake_interpolation_alpha(self, now=None):
        """Return the completed fraction of the current logical move interval."""
        interval = 1.0 / max(self.speed, 0.001)
        elapsed = (time.time() if now is None else now) - self.last_update_time
        return max(0.0, min(1.0, elapsed / interval))

    @staticmethod
    def _interpolate_snake(previous, current, alpha):
        """Interpolate existing segments only; never predict a future cell."""
        if not current:
            return []
        if not previous:
            previous = current
        positions = []
        for index, target in enumerate(current):
            start = previous[min(index, len(previous) - 1)]
            dx, dy = target[0] - start[0], target[1] - start[1]
            if abs(dx) + abs(dy) > 1:
                # A wrapped segment or a teleport never traverses the board.
                positions.append(target)
            else:
                positions.append((start[0] + dx * alpha, start[1] + dy * alpha))
        return positions

    def get_snake_render_positions(self, player=1, now=None):
        """Pixel positions derived exclusively from previous/current grid cells."""
        if self.player_count == 2:
            current = self.snake1 if player == 1 else self.snake2
            previous = self.previous_snake1 if player == 1 else self.previous_snake2
        else:
            current, previous = self.snake, self.previous_snake
        alpha = self.snake_interpolation_alpha(now)
        return [(x * GRID_SIZE, y * GRID_SIZE)
                for x, y in self._interpolate_snake(previous, current, alpha)]

    def get_snake_render_hitboxes(self, player=1, now=None):
        """Visual rectangles; gameplay collision remains on current grid cells."""
        return [pygame.Rect(round(x), round(y), GRID_SIZE, GRID_SIZE)
                for x, y in self.get_snake_render_positions(player, now)]

    def _move_snake(self, snake, new_head, invincible):
        """Commit a grid step, or lose a life when the destination stays occupied."""
        item_index = next((index for index, item in enumerate(self.items)
                           if (item.x, item.y) == new_head), None)
        occupied = snake[1:-1] if item_index is None else snake[1:]
        if not invincible and new_head in occupied:
            self.handle_self_collision()
            return False

        snake.insert(0, new_head)
        if item_index is None:
            snake.pop()
        else:
            self.handle_item_pickup(self.items[item_index])
            self.items.pop(item_index)
        return True

    def spawn_food(self):
        return self._spawn_item_in_free_cell(ItemType.FOOD)

    def _spawn_item_in_free_cell(self, item_type):
        occupied = set(self.snake1 + self.snake2 if self.player_count == 2 else self.snake)
        occupied.update((item.x, item.y) for item in self.items)
        if len(occupied) < GRID_WIDTH * GRID_HEIGHT:
            for _ in range(16):
                item = Item(item_type)
                if (item.x, item.y) not in occupied:
                    self.items.append(item)
                    return item
        free = [(x, y) for y in range(GRID_HEIGHT) for x in range(GRID_WIDTH)
                if (x, y) not in occupied]
        if not free:
            return None
        item = Item(item_type)
        item.x, item.y = random.choice(free)
        self.items.append(item)
        return item

    # --------------------------------------------------------------------
    # Gleichmäßiger Item-Spawn  –  jedes Item ≈ 9 %  (11 Einträge)
    # --------------------------------------------------------------------
    def spawn_new_item(self):
        # Liste der möglichen Items – Mehrfach­einträge = höhere Chance
        items = [
            ItemType.FOOD,
            ItemType.SPEED_BOOST,
            ItemType.SPEED_REDUCTION,
            ItemType.SCORE_BOOST,
            ItemType.INVINCIBILITY,
            ItemType.LENGTH_SHORTENER,
            ItemType.LENGTH_DOUBLE,
            ItemType.LOOT_BOX,
            ItemType.SPAWN_BOLBU,      #  → unsere Bolbu-Kapsel
            ItemType.DICE_EVENT,
            ItemType.SPECIAL_DAMAGE,
        ]

        itype = random.choice(items)
        if itype == ItemType.SPAWN_BOLBU:
            print("[DEBUG] Zufälliges SPAWN_BOLBU-Item erzeugt")

        return self._spawn_item_in_free_cell(itype)

    def level_up(self):
        self.level += 1
        self.experience -= self.exp_to_next_level
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
        self.speed = min(MAX_SPEED, self.speed + 0.5)
        self.start_boss_fight()
        self.score += 50 * self.level
        self.add_achievement(f"Level {self.level} erreicht!")

    def start_boss_fight(self):
        if self.boss is not None:
            return False
        boss_class = random.choice([Boss, Boss2])
        self.boss = boss_class(self.level, health_multiplier=self.settings['boss_health_multiplier'])
        self._boss_contact_ready_at.clear()
        self._spawn_item_in_free_cell(ItemType.PROJECTILE_SHOOT)
        self.add_achievement(self.boss.announcement)
        self.game_state = GameState.BOSS_FIGHT
        self.background = self.level_background_surface
        self.boss_fight_active = True
        boss_center = ((self.boss.x + self.boss.size / 2) * GRID_SIZE,
                       (self.boss.y + self.boss.size / 2) * GRID_SIZE)
        self.boss.aura_effect = self.effect_manager.spawn(
            "boss_aura", boss_center, {"loop": True, "lifetime": 60.0},
        )
        record_event(f"Bosskampf gestartet: Level {self.level}")
        return True

    def add_achievement(self, message):
        self.achievement_messages.append((message, time.time() + 10))

    def log_combat_event(self, event_type, **details):
        event = {"type": event_type, "time": time.time(), **details}
        self.combat_events.append(event)
        record_event(event_type + (f": {details}" if details else ""))

    def damage_boss(self, damage, source, *, is_projectile=True):
        """Apply boss damage and process the reward/transition exactly once."""
        boss = self.boss
        if boss is None:
            return False
        old_health = boss.health
        boss.health = max(0, boss.health - damage)
        self.log_combat_event("boss_damage", source=source, damage=old_health - boss.health,
                              health=boss.health)
        if is_projectile:
            self.log_combat_event("projectile_hit", projectile=source, target="boss")
        if boss.health > 0:
            return False
        center = boss.get_hitbox().center
        self.boss = None
        self.effect_manager.stop(getattr(boss, "aura_effect", None))
        self.boss_fight_active = False
        self.game_state = GameState.GAME
        self.boss_spawn_timer = time.time() + 60 + random.randint(0, 30)
        self.score += 100 * self.level
        self.add_achievement("Boss besiegt! Boss Down Easy Going !!")
        self.effects['boss_loot'] = time.time() + 10
        self.effect_manager.spawn("explosion", center)
        self.log_combat_event("boss_defeated", source=source, score=100 * self.level)
        return True

    def activate_portal(self, event):
        self.portal_effect_active = True
        self.portal_effect_end = time.time() + 60
        self.portal_spawn_cooldown = time.time() + 300
        self.portal_effect_type = event
        center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self.effect_manager.spawn("portal", center, {"lifetime": 1.2})
        # Portal visuals are transient and must never paint into the retained map.
        self.background = self.level_background_surface.copy()
        self.background.fill((random.randint(0,50), random.randint(0,50), random.randint(0,50)))
        for i in range(0, WINDOW_WIDTH, GRID_SIZE * 2):
            for j in range(0, WINDOW_HEIGHT, GRID_SIZE * 2):
                pygame.draw.rect(self.background,
                                 (random.randint(10,30), random.randint(10,30), random.randint(10,30)),
                                 (i, j, GRID_SIZE, GRID_SIZE))
        self.intro_bg = self.menu_bg.copy()
        if event == "teleport":
            if self.player_count == 2:
                self.snake1[0] = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
                self.snake2[0] = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            else:
                self.snake[0] = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            self._reset_snake_interpolation()
            self.add_achievement("Teleport!")
        elif event == "boss":
            if self.start_boss_fight():
                for _ in range(3):
                    self.spawn_new_item()
                self.add_achievement("Boss-Portal!")
            else:
                self.add_achievement("Bosskampf läuft bereits!")
        elif event == "loot":
            self.effects['score_boost'] = time.time() + 60
            self.add_achievement("Loot Boost!")
        elif event == "color_change":
            self.add_achievement("Mystery Colors!")
        elif event == "dice_event":
            self.dice_result = random.randint(1,20)
            self.dice_display_until = time.time() + 5
            if SOUNDS.get("dice"):
                SOUNDS["dice"].play()
            self.add_achievement(f"Portal Dice: {self.dice_result}")
            if self.dice_result > 10:
                self.score += self.dice_result * 5

    def spawn_independent_aoe_zone(self):
        from modules.aoe_zones import DamageZone, HealZone, DebuffZone
        pos = (random.randint(0, GRID_WIDTH - 1) * GRID_SIZE,
               random.randint(0, GRID_HEIGHT - 1) * GRID_SIZE)
        zone_radius = int(sqrt(0.1 * WINDOW_WIDTH * WINDOW_HEIGHT / 3.14))
        zone_type = random.choice(["damage", "heal", "slow"])
        duration = random.randint(5, 10)
        if zone_type == "damage":
            zone = DamageZone(pos, zone_radius, duration, (255, 0, 0, 128), effect_type="damage")
        elif zone_type == "heal":
            zone = HealZone(pos, zone_radius, duration, (0, 255, 0, 128), effect_type="heal")
        elif zone_type == "slow":
            zone = DebuffZone(pos, zone_radius, duration, (0, 0, 255, 128), effect_type="slow")
        else:
            zone = DamageZone(pos, zone_radius, duration, (255, 0, 0, 128), effect_type="damage")
        self.aoe_zones.append(zone)
        print(f"DEBUG: Independent {zone_type} zone spawned at {pos}")

    def update_projectiles(self):
        current_time = time.time()

        # ---- Portal Effect Timeout ----
        if self.portal_effect_active and current_time >= self.portal_effect_end:
            print("[DEBUG] Portal-Effekt endet")
            self.portal_effect_active = False
            self.portal_effect_type = None
        # Flammenprojektile und Cooldown aktualisieren
        if self.fireball_cooldown > 0:
            self.fireball_cooldown -= 1
        self.flame_projectiles = [p for p in self.flame_projectiles if p.update()]
        self.boss_flame_projectiles = [p for p in self.boss_flame_projectiles if p.update()]
        self.explosions = [e for e in self.explosions if e.update()]
        self.enemy_projectiles = [p for p in self.enemy_projectiles if p.update()]
        new_proj = []
        for proj in self.projectiles:
            dx, dy = proj['dir']
            new_x = proj['pos'][0] + dx
            new_y = proj['pos'][1] + dy
            proj['pos'] = (new_x, new_y)
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                continue
            if not proj.get("from_boss", False) and self._resolve_player_grid_projectile_hit(proj):
                continue
            new_proj.append(proj)
        self.projectiles = new_proj

    def _resolve_player_grid_projectile_hit(self, projectile):
        """Resolve collisions at the shot's new position and report consumption."""
        x, y = projectile["pos"]
        boss_hitbox = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        if self.boss and self.boss.get_rect().colliderect(boss_hitbox):
            self.damage_boss(PLAYER_PROJECTILE_DAMAGE,
                             projectile.get("projectile_type", "player_projectile"))
            return True

        snake = self.snake1 if self.player_count == 2 and self.snake1 else self.snake
        if not snake:
            return False
        head_x, head_y = snake[0]
        head_rect = pygame.Rect(head_x * GRID_SIZE, head_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        shot_rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE // 2, GRID_SIZE // 2)
        return head_rect.colliderect(shot_rect)

    def _player_heads_with_health(self):
        players = ((self.snake, "player_health"),) if self.player_count == 1 else (
            (self.snake1, "player_health_p1"), (self.snake2, "player_health_p2")
        )
        return [(snake[0], health_attr) for snake, health_attr in players if snake]

    def _resolve_classic_boss_projectile_hits(self):
        heads = [
            (pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE), health_attr)
            for (x, y), health_attr in self._player_heads_with_health()
        ]
        for projectile in self.projectiles:
            if not projectile.get("from_boss", False):
                continue
            x, y = projectile["pos"]
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            hit_players = projectile.get("hit_players", ())
            targets = tuple(
                health_attr for head, health_attr in heads
                if health_attr not in hit_players and head.colliderect(rect)
            )
            if not targets:
                continue

            projectile["hit_players"] = hit_players + targets
            lethal = False
            for health_attr in targets:
                health = getattr(self, health_attr) - CLASSIC_BOSS_PROJECTILE_DAMAGE
                setattr(self, health_attr, health)
                lethal = lethal or health <= 0
            if SOUNDS.get("damage"):
                SOUNDS["damage"].play()
            if lethal:
                # In 2P both heads take damage before resolving the shared life.
                self.handle_death()
                return

    def _resolve_fireball_hit(self, flame):
        """Apply the first confirmed hit and identify its target for the update."""
        hitbox = flame.get_hitbox()
        if self.boss and hitbox.colliderect(self.boss.get_hitbox().inflate(-10, -10)):
            self.damage_boss(flame.damage, "player_fireball")
            return "boss"

        for enemy in self.enemies:
            if time.time() - getattr(enemy, "spawn_time", 0) < 2:
                continue
            if hitbox.colliderect(enemy.get_hitbox()):
                enemy.health -= flame.damage
                if enemy.health <= 0:
                    self.enemies.remove(enemy)
                    self.score += 20
                    self.add_achievement("Enemy roasted!")
                return "enemy"
        return None

    def _resolve_boss_flame_hits(self, projectile):
        hit = False
        for (x, y), health_attr in self._player_heads_with_health():
            head_rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if projectile.collides_with(head_rect):
                setattr(self, health_attr, getattr(self, health_attr) - projectile.damage)
                hit = True
        return hit

    def check_boss_collision(self, snake_head):
        if self.boss:
            boss_rect = self.boss.get_rect()
            head_x = snake_head[0] * GRID_SIZE + GRID_SIZE // 2
            head_y = snake_head[1] * GRID_SIZE + GRID_SIZE // 2
            return boss_rect.collidepoint(head_x, head_y)
        return False

    def _resolve_boss_body_contact(self, now):
        if (self.boss is None or self.game_state == GameState.GAME_OVER
                or now < self.respawn_invincible_until
                or now - self.boss.spawn_time < BOSS_SPAWN_PROTECTION):
            return False

        targets = [
            health_attr for head, health_attr in self._player_heads_with_health()
            if now >= self._boss_contact_ready_at.get(health_attr, 0)
            and self.check_boss_collision(head)
        ]
        if not targets:
            return False

        for health_attr in targets:
            self._boss_contact_ready_at[health_attr] = now + BOSS_BODY_HIT_INTERVAL
            setattr(self, health_attr, getattr(self, health_attr) - BOSS_BODY_DAMAGE)
        if SOUNDS.get("damage"):
            SOUNDS["damage"].play()
        # Both players take their hit before the shared life can reset their health.
        if any(getattr(self, health_attr) <= 0 for health_attr in targets):
            self.handle_death()
        return True

    def auto_shoot_for_head(self, head, current_direction):
        slots = MAX_PLAYER_GRID_PROJECTILES - sum(not shot.get("from_boss", False)
                                                  for shot in self.projectiles)
        if slots <= 0:
            return
        target = None
        min_dist = float("inf")
        for enemy in self.enemies:
            if time.time() - getattr(enemy, 'spawn_time', 0) < 3:
                continue
            dist = sqrt((head[0] - enemy.x) ** 2 + (head[1] - enemy.y) ** 2)
            if dist < min_dist:
                min_dist = dist
                target = enemy
        if target:
            dx = target.x - head[0]
            dy = target.y - head[1]
            angle = atan2(dy, dx)
            dir_x = cos(angle) * self.settings['projectile_speed_factor']
            dir_y = sin(angle) * self.settings['projectile_speed_factor']
        else:
            dir_x = current_direction.value[0] * self.settings['projectile_speed_factor']
            dir_y = current_direction.value[1] * self.settings['projectile_speed_factor']
        proj = {'pos': (head[0], head[1]), 'dir': (dir_x, dir_y), "effect": "damage",
                "projectile_type": "player_projectile"}
        self.projectiles.append(proj)
        self.log_combat_event("projectile_fired", projectile="player_projectile")
        for _ in range(min(self.extra_auto_shots, slots - 1)):
            deviation = random.uniform(-0.3, 0.3)
            proj_extra = {'pos': (head[0], head[1]),
                          'dir': (dir_x + deviation, dir_y + deviation),
                          "effect": "damage", "projectile_type": "multishot"}
            self.projectiles.append(proj_extra)
            self.log_combat_event("projectile_fired", projectile="multishot")

    def auto_shoot(self):
        current_time = time.time()
            # Prüft, ob der Effekt noch aktiv ist
        if self.effects['projectile_shoot'] > current_time:
            if self.player_count == 1:
                # Verwende den konfigurierten Auto-Shoot-Intervall statt 3 Sekunden
                if current_time - self.last_auto_shoot < self.settings.get('auto_shoot_interval', 0.5):
                    return
                self.last_auto_shoot = current_time
                self.auto_shoot_for_head(self.snake[0], self.snake_direction)
            elif self.player_count == 2:
                if self.snake1 and current_time - self.last_auto_shoot1 >= self.settings.get('auto_shoot_interval', 0.5):
                    self.last_auto_shoot1 = current_time
                    self.auto_shoot_for_head(self.snake1[0], self.snake_direction1)
                if self.snake2 and current_time - self.last_auto_shoot2 >= self.settings.get('auto_shoot_interval', 0.5):
                    self.last_auto_shoot2 = current_time
                    self.auto_shoot_for_head(self.snake2[0], self.snake_direction2)

    # === Haupt‑Update‑Schleife ===============================================
    def update(self):
        if self.admin_panel.active or self.level_editor.active:
            return
        current_time = time.time()
        effect_now = time.monotonic()
        self.effect_manager.update(effect_now - self._effect_update_time)
        self._effect_update_time = effect_now
        # === [KS_FIX: PORTAL VISUAL RESTORE] ===
        if self.portal_effect_active and current_time >= self.portal_effect_end:
            print("[DEBUG] Portal-Effekt endet")
            self.portal_effect_active = False
            self.portal_effect_type = None
            self.build_background_from_map()
            self.background = self.level_background_surface
            print("[DEBUG] Editor-Karte neu geladen und gesetzt.")

        # ───────────────────────── 1) Cooldowns & Auto‑Shoot ─────────────────────────
        if self.fireball_cooldown_p1 > 0:
            self.fireball_cooldown_p1 -= 1
        if self.fireball_cooldown_p2 > 0:
            self.fireball_cooldown_p2 -= 1
        if self.fireball_cooldown > 0:
            self.fireball_cooldown -= 1
        # Flammen­geschosse leben lassen / entfernen
        self.flame_projectiles = [p for p in self.flame_projectiles if p.update()]
        self.boss_flame_projectiles = [p for p in self.boss_flame_projectiles if p.update()]

        invincible = current_time < self.respawn_invincible_until
        if self.effects['projectile_shoot'] > current_time:
            self.auto_shoot()
            # -- Gegner-Spawn ---------------------------------------------
            if (random.random() < self.settings['enemy_spawn_rate']
                    and len(self.enemies) < ENEMY_LIMIT[self.player_count]):
                enemy = NormalEnemy()
                enemy.spawn_time = time.time()
                self.enemies.append(enemy)
#             enemy.spawn_time = time.time()    # removed by patch to avoid UnboundLocalError
#             self.enemies.append(enemy)    # removed by patch to avoid UnboundLocalError

        for enemy in self.enemies:
            # Pass Spielerposition für smartere Gegner
            if self.player_count == 1 and self.snake:
                px, py = self.snake[0]
            elif self.player_count == 2 and self.snake1:
                px, py = self.snake1[0]
            else:
                px = py = None
            enemy.update(px, py)
            if hasattr(enemy, 'projectiles'):
                slots = max(0, MAX_ENEMY_PROJECTILES - len(self.enemy_projectiles))
                admitted = enemy.projectiles[:slots]
                self.enemy_projectiles.extend(admitted)
                for _ in admitted:
                    self.log_combat_event("projectile_fired", projectile="bolbu_projectile")
                enemy.projectiles.clear()

        # ───────────────────────── 3) Kollisions­prüfungen ───────────────────────────
            # --- Sichere Kollisionsprüfung für klassische Projektile ---
        for enemy in self.enemies[:]:
            enemy_rect = enemy.get_hitbox()
            if current_time - getattr(enemy, 'spawn_time', 0) < 3:
                continue
            for proj in self.projectiles:
                proj_rect = pygame.Rect(
                    proj['pos'][0] * GRID_SIZE,
                    proj['pos'][1] * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE
                )
                if enemy_rect.colliderect(proj_rect):
                    enemy.health -= 1
                    if enemy.health <= 0 and enemy in self.enemies:
                        self.enemies.remove(enemy)
                        self.score += 20
                        self.add_achievement("!")
                    if SOUNDS.get("gegner"):
                        SOUNDS["gegner"].play()
                    if self.portal is None and current_time >= self.portal_spawn_cooldown:
                        self.portal = Portal()
                    break

        # ---------- 3a)  **FlameProjectile**  ----------
        for flame in self.flame_projectiles[:]:
            hit = self._resolve_fireball_hit(flame)
            if hit is not None:
                self.spawn_fire_explosion(flame.rect.center)
                self.flame_projectiles.remove(flame)
                if hit == "boss":
                    break


            
        # [KS_TAG: BOSS_FLAME_COLLISION]        # ----- ENEMY PROJECTILE COLLISION -----
        for proj in self.enemy_projectiles[:]:
            if self.player_count == 1 and self.snake:
                head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if proj.rect.colliderect(head_rect):
                    self.spawn_fire_explosion(proj.rect.center)
                    self.player_health -= proj.damage
                    if proj in self.enemy_projectiles:
                     self.enemy_projectiles.remove(proj)
            elif self.player_count == 2:
                for snake, attr in [(self.snake1, 'player_health_p1'), (self.snake2, 'player_health_p2')]:
                    if snake:
                        head_rect = pygame.Rect(snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                        if proj.rect.colliderect(head_rect):
                            self.spawn_fire_explosion(proj.rect.center)
                            current = getattr(self, attr)
                            setattr(self, attr, current - proj.damage)
                            if proj in self.enemy_projectiles:
                             self.enemy_projectiles.remove(proj)
        for proj in self.boss_flame_projectiles[:]:
            if self._resolve_boss_flame_hits(proj):
                self.spawn_fire_explosion(proj.rect.center)
                self.boss_flame_projectiles.remove(proj)


        # … (Spieler‑ und Boss‑Kollisionen, AoE‑Handling, Bewegung,
        #     Item‑Aufnahme, Boss‑Logik, Projektil‑Update usw. – unverändert wie besprochen) …
        # Kollisionsprüfung Spieler (Singleplayer)
        if self.player_count == 1 and self.snake:
            head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE,
                                    self.snake[0][1] * GRID_SIZE,
                                    GRID_SIZE, GRID_SIZE)
            if self.portal and head_rect.colliderect(self.portal.get_rect()):
                self.activate_portal(self.portal.event)
                self.portal_effect_active = True
                self.portal = None
            # Prüfe, ob der Spieler stillsteht (kein Positionswechsel)
            current_head = self.snake[0]
            if self.last_head_pos is None or current_head != self.last_head_pos:
                # Bewegung festgestellt → Timer zurücksetzen
                self.last_head_pos = current_head
                self.still_timer = None
            else:
                # Kein Positionswechsel – Timer starten bzw. fortschreiben
                if self.still_timer is None:
                    self.still_timer = current_time
                else:
                    still_elapsed = current_time - self.still_timer
                    # Zeige den Countdown an (2,5 Sek. Gesamtzeit)
                    countdown = max(0.0, 2.5 - still_elapsed)
                    countdown_text = pygame.font.SysFont('Arial', 40, bold=True).render(f"{countdown:.1f}", True, RED)
                    self.screen.blit(countdown_text, ((WINDOW_WIDTH - countdown_text.get_width()) // 2,
                                                      (WINDOW_HEIGHT - countdown_text.get_height()) // 2))
                    # Wenn der Spieler insgesamt 2,5 Sek. stillgestanden hat → Respawn auslösen
                    if still_elapsed >= 2.5:
                        self.handle_self_collision()
                        self.still_timer = None  # Timer zurücksetzen, damit nicht mehrfach ausgelöst wird

            # Zusätzlich die herkömmliche Kollisionsprüfung mit Gegnern:
            # (Falls der Kopf mit einem Gegner kollidiert)
            for enemy in self.enemies:
                if not invincible and head_rect.colliderect(enemy.get_hitbox()):
                    self.player_health -= 10
                    if self.player_health <= 0:
                        self.handle_death()
                    break
        elif self.player_count == 2:
            # Mehrspieler-Kollisionen (unverändert)
            for snake, health_attr in [(self.snake1, 'player_health_p1'),
                                         (self.snake2, 'player_health_p2')]:
                if snake:
                    head_rect = pygame.Rect(snake[0][0] * GRID_SIZE,
                                            snake[0][1] * GRID_SIZE,
                                            GRID_SIZE, GRID_SIZE)
                    if self.portal and head_rect.colliderect(self.portal.get_rect()):
                        self.activate_portal(self.portal.event)
                        self.portal_effect_active = True
                        self.portal = None
                    for enemy in self.enemies:
                        if not invincible and head_rect.colliderect(enemy.get_hitbox()):
                            current_health = getattr(self, health_attr)
                            current_health -= 10
                            setattr(self, health_attr, current_health)
                            if current_health <= 0:
                                self.handle_death()
                            break
        if self._resolve_boss_body_contact(current_time):
            invincible = current_time < self.respawn_invincible_until
        if self.projectiles and current_time >= self.respawn_invincible_until and self.game_state != GameState.GAME_OVER:
            self._resolve_classic_boss_projectile_hits()
            invincible = current_time < self.respawn_invincible_until
        self.update_projectiles()
        if self.game_state == GameState.GAME_OVER:
            return
        if self.player_count == 1 and self.snake:
            player_obj = type("Player", (), {})()
            player_obj.pos = Vector2(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE)
            player_obj.health = self.player_health
            player_obj.base_speed = 5
            player_obj.speed = 5
            for zone in self.aoe_zones:
                zone.update()
                if zone.is_inside(player_obj.pos) and not invincible:
                    zone.apply_effect(player_obj)
                    if not hasattr(zone, "debug_triggered"):
                        print(f"DEBUG: AoE-Effekt '{zone.effect_type}' auf Singleplayer angewendet.")
                        zone.debug_triggered = True
            self.player_health = player_obj.health
            if self.player_health <= 0:
                self.handle_death()
        elif self.player_count == 2 and self.snake1 and self.snake2:
            p1_obj = type("Player", (), {})()
            p1_obj.pos = Vector2(self.snake1[0][0] * GRID_SIZE, self.snake1[0][1] * GRID_SIZE)
            p1_obj.health = self.player_health_p1
            p1_obj.base_speed = 5
            p1_obj.speed = 5
            for zone in self.aoe_zones:
                zone.update()
                if zone.is_inside(p1_obj.pos) and not invincible:
                    zone.apply_effect(p1_obj)
                    if not hasattr(zone, "debug_triggered_p1"):
                        print(f"DEBUG: AoE-Effekt '{zone.effect_type}' auf Spieler 1 angewendet.")
                        zone.debug_triggered_p1 = True
            self.player_health_p1 = p1_obj.health
            if self.player_health_p1 <= 0:
                self.handle_death()
            p2_obj = type("Player", (), {})()
            p2_obj.pos = Vector2(self.snake2[0][0] * GRID_SIZE, self.snake2[0][1] * GRID_SIZE)
            p2_obj.health = self.player_health_p2
            p2_obj.base_speed = 5
            p2_obj.speed = 5
            for zone in self.aoe_zones:
                zone.update()
                if zone.is_inside(p2_obj.pos) and not invincible:
                    zone.apply_effect(p2_obj)
                    if not hasattr(zone, "debug_triggered_p2"):
                        print(f"DEBUG: AoE-Effekt '{zone.effect_type}' auf Spieler 2 angewendet.")
                        zone.debug_triggered_p2 = True
            self.player_health_p2 = p2_obj.health
            if self.player_health_p2 <= 0:
                self.handle_death()
        self.aoe_zones = [zone for zone in self.aoe_zones if zone.alive]
        if random.random() < 0.001 and len(self.aoe_zones) < 5:
            self.spawn_independent_aoe_zone()
        delta = current_time - self.last_update_time
        if delta >= 1.0 / self.speed:
            self._capture_previous_snakes()
            self.last_update_time = current_time
            self_collision_protected = invincible or current_time < self.effects["invincibility"]
            if self.player_count == 2:
                if self.portal and self.snake1:
                    head_rect = pygame.Rect(self.snake1[0][0] * GRID_SIZE, self.snake1[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if head_rect.colliderect(self.portal.get_rect()):
                        self.activate_portal(self.portal.event)
                        self.portal_effect_active = True
                        self.portal = None
                if self.snake1:
                    head1 = self.snake1[0]
                    self.snake_direction1 = self.next_direction1 if hasattr(self, 'next_direction1') else Direction.RIGHT
                    new_head1 = ((head1[0] + self.snake_direction1.value[0]) % GRID_WIDTH,
                                 (head1[1] + self.snake_direction1.value[1]) % GRID_HEIGHT)
                    if not self._move_snake(self.snake1, new_head1, self_collision_protected):
                        return
                    self.metrics.apply_direction(1, self.snake_direction1)
                if self.snake2:
                    head2 = self.snake2[0]
                    self.snake_direction2 = self.next_direction2 if hasattr(self, 'next_direction2') else Direction.RIGHT
                    new_head2 = ((head2[0] + self.snake_direction2.value[0]) % GRID_WIDTH,
                                 (head2[1] + self.snake_direction2.value[1]) % GRID_HEIGHT)
                    if not self._move_snake(self.snake2, new_head2, self_collision_protected):
                        return
                    self.metrics.apply_direction(2, self.snake_direction2)
            else:
                if self.portal and self.snake:
                    head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if head_rect.colliderect(self.portal.get_rect()):
                        self.activate_portal(self.portal.event)
                        self.portal_effect_active = True
                        self.portal = None
                if self.snake:
                    head = self.snake[0]
                    self.snake_direction = self.next_direction if hasattr(self, 'next_direction') else Direction.RIGHT
                    new_head = ((head[0] + self.snake_direction.value[0]) % GRID_WIDTH,
                               (head[1] + self.snake_direction.value[1]) % GRID_HEIGHT)
                    if not self._move_snake(self.snake, new_head, self_collision_protected):
                        return
                    self.metrics.apply_direction(1, self.snake_direction)
            if self.boss:
                if current_time - self.boss.spawn_time >= BOSS_SPAWN_PROTECTION:
                    if self._resolve_boss_body_contact(current_time):
                        invincible = current_time < self.respawn_invincible_until
                    if self.game_state != GameState.GAME_OVER:
                        act = self.boss.update(current_time)
                        if act == "aoe":

                            from modules.aoe_zones import GrowingBossAOEZone
                            zone = GrowingBossAOEZone(
                                (self.boss.x * GRID_SIZE + (self.boss.size * GRID_SIZE) // 2,
                                 self.boss.y * GRID_SIZE + (self.boss.size * GRID_SIZE) // 2),
                                int(GRID_SIZE * 1.2),
                                int(GRID_SIZE * 2.5),
                                duration=4.0,
                                color=(255, 0, 0, 150),
                                effect_type="damage",
                                source="boss"
                            )
                            self.aoe_zones.append(zone)
                            boss_rect = self.boss.get_rect()
                            target = self.snake[0] if self.player_count == 1 and self.snake else (self.snake1[0] if self.player_count == 2 and self.snake1 else None)
                            if target:
                                head_pixel = (target[0] * GRID_SIZE + GRID_SIZE // 2, target[1] * GRID_SIZE + GRID_SIZE // 2)
                                if boss_rect.inflate(40, 40).collidepoint(head_pixel) and not invincible:
                                    if SOUNDS.get("damage"):
                                        SOUNDS["damage"].play()
                                    self.handle_death()
                        elif act == "boss_shoot":
                            self.boss_shoots_flame()
                            target = self.snake[0] if self.player_count == 1 and self.snake else (self.snake1[0] if self.player_count == 2 and self.snake1 else None)
                            if (target and not invincible
                                    and sum(shot.get("from_boss", False) for shot in self.projectiles)
                                    < MAX_BOSS_GRID_PROJECTILES):
                                dx = 1 if target[0] > self.boss.x else -1 if target[0] < self.boss.x else 0
                                dy = 1 if target[1] > self.boss.y else -1 if target[1] < self.boss.y else 0
                                boss_proj_img = random.choice(BOSS_PROJECTILES) if BOSS_PROJECTILES else PROJECTILE_IMG
                                proj = {'pos': (self.boss.x, self.boss.y),
                                        'dir': (dx * self.settings['projectile_speed_factor'], dy * self.settings['projectile_speed_factor']),
                                        "effect": "damage",
                                        "from_boss": True,
                                        "projectile_type": "boss_projectile",
                                        "image": boss_proj_img,
                                        "scale": self.boss.size}
                                self.projectiles.append(proj)
                                self.log_combat_event("projectile_fired", projectile="boss_projectile")
            if random.random() < 0.005 * self.settings['difficulty'] and len(self.items) < 5:
                self.spawn_new_item()
            self.update_projectiles()

             #  Admin-Shortcut: Item exakt an Koordinate spawnen
    def spawn_item_at(self, item_type, grid_x, grid_y):
        """
        Wird vom Admin-Panel (Button 6) benutzt, um z.B. ein SPAWN_BOLBU-Item
        direkt neben dem Schlangenkopf zu erzeugen.
        """
        if not hasattr(self, "items"):
            return
        # Spielfeldbegrenzung
        grid_x = max(0, min(int(grid_x), GRID_WIDTH  - 1))
        grid_y = max(0, min(int(grid_y), GRID_HEIGHT - 1))

        # Vermeide Spawn auf Kopf-Segment
        occ = (self.snake1 + self.snake2) if self.player_count == 2 else self.snake
        if (grid_x, grid_y) in occ:
            grid_y = (grid_y + 1) % GRID_HEIGHT

        item = Item(item_type)
        item.x, item.y = grid_x, grid_y
        self.items.append(item)
        print(f"[ADMIN] Item {item_type.name} gespawnt an ({grid_x},{grid_y})")

        # Ende Update
    def handle_item_pickup(self, item):
        current_time = time.time()
        if SOUNDS.get("eat"):
            SOUNDS["eat"].play()
        if item.type == ItemType.FOOD:
            self.score += 10
            self.experience += 10
            self.spawn_food()
        elif item.type == ItemType.SPEED_BOOST:
            self.speed = min(MAX_SPEED, self.speed + 3)
            self.effects['speed_boost'] = current_time + 5
            self.score += 15
            self.experience += 15
        elif item.type == ItemType.SPEED_REDUCTION:
            self.speed = max(1, self.speed - 3)
            self.effects['speed_reduction'] = current_time + 5
            self.score += 15
            self.experience += 15
        elif item.type == ItemType.SCORE_BOOST:
            self.score += 50
            self.experience += 20
        elif item.type == ItemType.INVINCIBILITY:
            self.effects['invincibility'] = current_time + 10
            self.score += 25
            self.experience += 25
        elif item.type == ItemType.LOOT_BOX:
            if SOUNDS.get("powerup"):
                SOUNDS["powerup"].play()
            rewards = [kind for kind in ItemType
                       if kind not in (ItemType.LOOT_BOX, ItemType.SPAWN_BOLBU)]
            self.handle_item_pickup(Item(random.choice(rewards)))
            self.score += 20
            self.experience += 20
        elif item.type == ItemType.LENGTH_SHORTENER:
            self.effects['length_shortener'] = current_time + 8
            self.score += 30
            self.experience += 15
        elif item.type == ItemType.LENGTH_DOUBLE:
            self.effects['length_double'] = current_time + 8
            self.score += 30
            self.experience += 15
        elif item.type == ItemType.DICE_EVENT:
            if SOUNDS.get("dice"):
                SOUNDS["dice"].play()
            self.dice_result = random.randint(1, 20)
            self.dice_display_until = current_time + 5
            if self.dice_result == 1:
                self.add_achievement("Kritischer Fehlschlag!")
                self.score += 1
            elif self.dice_result == 20:
                self.add_achievement("Kritischer Erfolg!")
                self.score += 300
                self.experience = self.exp_to_next_level
            elif self.dice_result > 15:
                self.add_achievement("Großer Erfolg!")
                self.score += self.dice_result * 5
                self.experience += self.dice_result * 2
            elif self.dice_result > 10:
                self.add_achievement("Erfolg!")
                self.score += self.dice_result * 3
                self.experience += self.dice_result
            elif self.dice_result > 5:
                self.add_achievement("Kleiner Erfolg!")
                self.score += self.dice_result * 2
                self.experience += self.dice_result // 2
            else:
                self.add_achievement("Fehlschlag!")
                self.score += self.dice_result
        elif item.type == ItemType.SPECIAL_DAMAGE:
            if (self.boss is not None
                    and current_time - self.last_boss_effect_time >= self.boss_effect_cooldown):
                self.last_boss_effect_time = current_time
                if SOUNDS.get("powerup"):
                    SOUNDS["powerup"].play()
                self.score += 100
                self.damage_boss(5 * self.level, "special_damage_item", is_projectile=False)
        
        elif item.type == ItemType.SPAWN_BOLBU:
            print('[DEBUG] SPAWN_BOLBU Item aufgenommen')
            from modules.bolbu_enemy import BolbuEnemy
            slots = max(0, ENEMY_LIMIT[self.player_count] - len(self.enemies))
            spawn_count = min(random.randint(1, 3), slots)
            if not spawn_count:
                self.add_achievement("Gegnerlimit erreicht")
            for _ in range(spawn_count):
                bolbu = BolbuEnemy()
                bolbu.spawn_time = current_time
                self.enemies.append(bolbu)
            self.score += 25 * spawn_count
            self.add_achievement(f"{spawn_count} Bolbu gespawnt!")

        elif item.type == ItemType.PROJECTILE_SHOOT:
            self.effects['projectile_shoot'] = max(self.effects['projectile_shoot'], current_time) + 900
            self.extra_auto_shots = min(6, self.extra_auto_shots + 1)
            self.score += 40
            self.experience += 20
            self.add_achievement("Multi-Shoot aktiviert!")
        if self.experience >= self.exp_to_next_level:
            self.level_up()

    def handle_self_collision(self):
        # Spiele den Schadens-Sound (sofern vorhanden)
        if SOUNDS.get("damage"):
            SOUNDS["damage"].play()
        # Ziehe ein Leben ab, aber nur, wenn noch Leben übrig sind
        self.lives -= 1
        print("DEBUG: Selbstkollision erkannt – Leben abgezogen, verbleibende Leben:", self.lives)
    
        # Falls noch Leben vorhanden, respawne die Schlange (nur im Singleplayer; in Mehrspieler anpassen)
        if self.lives > 0:
            if self.player_count == 1:
                self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
                self.snake_direction = Direction.RIGHT
                self.next_direction = Direction.RIGHT
                self.player_health = 100  # Setze den Gesundheitswert zurück
            else:
                # Für Mehrspieler können ähnlich beide Schlangen zurückgesetzt werden
                self.snake1 = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
                self.snake2 = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
                self.snake_direction1 = Direction.RIGHT
                self.snake_direction2 = Direction.RIGHT
                self.next_direction1 = Direction.RIGHT
                self.next_direction2 = Direction.RIGHT
                self.player_health_p1 = 100
                self.player_health_p2 = 100
            # Setze eine kurze Invincibility, um erneute sofortige Kollision zu vermeiden
            self._reset_snake_interpolation()
            self.respawn_invincible_until = time.time() + 3
        else:
            # Falls keine Leben mehr vorhanden sind, gehe auf Game Over
            self.metrics.cancel_pending()
            self.game_state = GameState.GAME_OVER
            self.game_over_time = time.time()
        if len(self.leaderboard) < 10 or self.score > self.leaderboard[-1][1]:
            self.leaderboard_mode = True

    def handle_death(self):
        if self.game_state == GameState.GAME_OVER:
            return
        if self.player_count == 1:
            if self.player_health > 0:
                return
        elif self.player_count == 2:
            if self.player_health_p1 > 0 and self.player_health_p2 > 0:
                return
        if SOUNDS.get("gameover"):
            SOUNDS["gameover"].play()
        snake = self.snake if self.player_count == 1 else self.snake1
        if snake:
            self.effect_manager.spawn(
                "death", ((snake[0][0] + 0.5) * GRID_SIZE,
                          (snake[0][1] + 0.5) * GRID_SIZE), {"lifetime": 1.0})
        self.lives -= 1
        if self.lives <= 0:
            self.metrics.cancel_pending()
            self.game_state = GameState.GAME_OVER
            self.game_over_time = time.time()
            if len(self.leaderboard) < 10 or self.score > self.leaderboard[-1][1]:
                self.leaderboard_mode = True
        else:
            if self.player_count == 2:
                self.snake1 = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
                self.snake2 = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
                self.snake_direction1 = Direction.RIGHT
                self.snake_direction2 = Direction.RIGHT
                self.next_direction1 = Direction.RIGHT
                self.next_direction2 = Direction.RIGHT
                self.player_health_p1 = 100
                self.player_health_p2 = 100
            else:
                self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
                self.snake_direction = Direction.RIGHT
                self.next_direction = Direction.RIGHT
                self.player_health = 100
            self._reset_snake_interpolation()
            self.respawn_invincible_until = time.time() + 3

    def handle_events(self):
        events = pygame.event.get()
        read_ns = self.metrics.stamp()
        for event in events:
            if event.type == pygame.QUIT:
                sys.exit()
            if self.game_state == GameState.CONTROLS:
                self.controls_menu.handle_event(event)
                continue
            actions = self.input.actions_for(event, player_count=self.player_count)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.level_editor.active = False
                self.admin_panel.toggle()
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                self.admin_panel.close()
                self.level_editor.toggle()
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.admin_panel.active:
                    self.admin_panel.close()
                    continue
                if self.level_editor.active:
                    self.level_editor.toggle()
                    continue
            # An open developer tool owns all input; gameplay never sees it.
            if self.admin_panel.active:
                self.admin_panel.handle_event(event)
                continue
            if self.level_editor.active:
                self.level_editor.handle_event(event)
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.game_state not in (GameState.GAME, GameState.BOSS_FIGHT):
                    self.set_state(self.intro_state())
            if self.game_state == GameState.SETTINGS:
                self.options_menu.handle_event(event)
            elif self.game_state == GameState.SIMULATION:
                self.simulation_menu.handle_event(event)
            elif self.game_state == GameState.CUSTOMIZATION:
                self.custom_menu.handle_event(event)
            elif self.game_state == GameState.INTRO:
                if "menu_accept" in actions:
                    self.intro_buttons[self.intro_focus].action()
                    continue
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_DOWN, pygame.K_TAB):
                    self.intro_focus = (self.intro_focus + 1) % len(self.intro_buttons)
                    continue
                if event.type == pygame.KEYDOWN and event.key == pygame.K_UP:
                    self.intro_focus = (self.intro_focus - 1) % len(self.intro_buttons)
                    continue
                for btn in self.intro_buttons:
                    btn.check_hover(pygame.mouse.get_pos())
                    btn.handle_event(event)
            elif self.game_state == GameState.PAUSE:
                if "pause" in actions:
                    self._resume_game()
                    continue
                for btn in self.pause_buttons:
                    btn.check_hover(pygame.mouse.get_pos())
                    btn.handle_event(event)
            elif self.game_state == GameState.GAME_OVER:
                if self.leaderboard_mode:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_BACKSPACE:
                            self.name_input = self.name_input[:-1]
                        elif event.key == pygame.K_RETURN:
                            with open(user_data_path(LEADERBOARD_FILE), "a", encoding="utf-8") as f:
                                f.write(f"{self.name_input},{self.score}\n")
                            self.leaderboard = self.load_leaderboard()
                            self.leaderboard_mode = False
                            self.reset_game()
                        else:
                            self.name_input += event.unicode
                else:
                    for btn in self.game_over_buttons:
                        btn.check_hover(pygame.mouse.get_pos())
                        btn.handle_event(event)
            elif self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
                if actions:
                    self._apply_gameplay_actions(actions, read_ns)
                elif event.type == pygame.KEYDOWN:
                    self._handle_debug_key(event.key)

    def _apply_gameplay_actions(self, actions, read_ns=None):
        if "pause" in actions:
            self.set_state(GameState.PAUSE)
            return

        players = (("", self.snake),) if self.player_count == 1 else (
            ("1", self.snake1), ("2", self.snake2))
        for player, (suffix, snake) in enumerate(players, start=1):
            direction = getattr(self, f"snake_direction{suffix}")
            next_direction = f"next_direction{suffix}"
            for name, requested in DIRECTION_ACTIONS.items():
                if f"p{player}_{name}" not in actions:
                    continue
                if requested == OPPOSITE_DIRECTION[direction]:
                    self.metrics.reject("direction", "Gegenrichtung")
                    continue
                queued = getattr(self, next_direction)
                if requested == queued:
                    self.metrics.reject("direction", "unverändert")
                    continue
                if requested == direction:
                    self.metrics.discard_direction(player)
                else:
                    self.metrics.accept_direction(player, requested, read_ns)
                setattr(self, next_direction, requested)

            cooldown = f"fireball_cooldown_p{player}"
            if f"p{player}_fire" not in actions:
                continue
            if not snake:
                self.metrics.reject("fire", "keine Schlange")
                continue
            if getattr(self, cooldown) > 0:
                self.metrics.reject("fire", "cooldown")
                continue
            accepted_ns = self.metrics.stamp()
            x, y = snake[0]
            projectile = FlameProjectile(x * GRID_SIZE, y * GRID_SIZE, direction.value)
            self.flame_projectiles.append(projectile)
            setattr(self, cooldown, FPS * PLAYER_FIREBALL_COOLDOWN_SECONDS)
            self.metrics.apply_fire(projectile, read_ns, accepted_ns)
            self.log_combat_event("projectile_fired", projectile="player_fireball", player=player)

        if "special_effect" in actions:
            self._spawn_special_effect()

    def _spawn_special_effect(self):
        from modules.aoe_zones import BackgroundEffectZone

        path = asset_path("graphics", "AOEEffekte", "Backround0021.png")
        try:
            image = pygame.image.load(path).convert_alpha()
        except (OSError, pygame.error) as exc:
            record_event(f"Spezialeffekt konnte nicht geladen werden: {exc}")
            return
        self.aoe_zones.insert(0, BackgroundEffectZone(image, 7))

    def _handle_debug_key(self, key):
        if key not in (pygame.K_r, pygame.K_t, pygame.K_z, pygame.K_u, pygame.K_i, pygame.K_o):
            return
        snake = self.snake if self.player_count == 1 else self.snake1
        if not snake:
            return
        x, y = snake[0]
        pos = (x * GRID_SIZE, y * GRID_SIZE)
        radius = int(sqrt(0.25 * WINDOW_WIDTH * WINDOW_HEIGHT / pi))

        if key == pygame.K_r:
            zone = DamageZone(pos, radius, 5, (255, 0, 0, 128), effect_type="damage")
        elif key == pygame.K_t:
            zone = DebuffZone(pos, radius, 6, (0, 0, 255, 128), effect_type="slow")
        elif key == pygame.K_z:
            zone = HealZone(pos, radius, 8, (0, 255, 0, 128), effect_type="heal")
        elif key == pygame.K_u:
            zone = FollowZone(Vector2(pos), radius, 10, (255, 0, 255, 128), effect_type="aura")
        else:
            from modules.aoe_zones import get_aoe_effect

            image = get_aoe_effect()
            if key == pygame.K_i:
                if image is None:
                    return
                zone = AoEZone(pos, radius, 7, (255, 255, 255, 128), effect_type="special")
            else:
                zone = AoEZone(pos, radius, 7, (200, 200, 200, 128), effect_type="extra")
            zone.image = image
        self.aoe_zones.append(zone)

    def draw(self):
        start = self.metrics.stamp()
        self._render()
        if (self.metrics.enabled and not self.admin_panel.active and not self.level_editor.active
                and self.game_state in (GameState.GAME, GameState.BOSS_FIGHT)):
            self.metrics.draw(self.screen)
        before_present = self.metrics.stamp()
        pygame.display.update()
        presented = self.metrics.stamp()
        self.metrics.record_phase("draw", start, before_present)
        self.metrics.record_phase("present", before_present, presented)
        self.metrics.finish_frame(presented)

    def _render(self):
        if self.level_editor.active:
            self.level_editor.draw(self.screen)
            return
        if self.game_state == GameState.INTRO:
            self.draw_intro()
        elif self.game_state == GameState.CONTROLS:
            self.controls_menu.draw(self.screen)
        elif self.game_state == GameState.CUSTOMIZATION:
            self.custom_menu.draw(self.screen)
        elif self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
            self.draw_game(include_hud=False)
        elif self.game_state == GameState.PAUSE:
            self.draw_game(include_hud=False)
            self.draw_pause()
        elif self.game_state == GameState.GAME_OVER:
            self.draw_game(include_hud=False)
            self.draw_game_over()
        elif self.game_state == GameState.SETTINGS:
            self.options_menu.draw(self.screen)
        elif self.game_state == GameState.LEADERBOARD:
            self.draw_leaderboard()
        elif self.game_state == GameState.SIMULATION:
            self.simulation_menu.draw(self.screen)
        if self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
            if self.boss_spawn_timer > time.time():
                cooldown = int(self.boss_spawn_timer - time.time())
                cd_txt = pygame.font.SysFont('Arial', 16, bold=True).render(f"Boss spawn in: {cooldown}s", True, ORANGE)
                self.screen.blit(cd_txt, (10, WINDOW_HEIGHT - 30))
        if self.game_state in (GameState.GAME, GameState.BOSS_FIGHT, GameState.PAUSE, GameState.GAME_OVER):
            self.draw_hud()
            self.achievement_manager.draw_achievements(self.screen)
            self.achievement_manager.draw_portal_event(self.screen)
        self.admin_panel.draw(self.screen)

    def draw_hud(self):
        score_txt = pygame.font.SysFont('Arial', 30).render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_txt, (20, 10))
        for i in range(self.lives):
            pygame.draw.rect(self.screen, RED, (WINDOW_WIDTH - 35 - i * 30, 15, 20, 20))
        level_txt = pygame.font.SysFont('Arial', 20).render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_txt, (20, 45))
        if self.player_count == 1:
            self.draw_health_bar()
        elif self.player_count == 2:
            draw_health_bar_two(self)

    def draw_health_bar(self):
        bar_width = 200
        bar_height = 20
        x = 20
        y = 80
        health_percent = max(0, min(1.0, self.player_health / 100.0))
        if health_percent > 0.5:
            red = int((1 - health_percent) * 2 * 255)
            green = 255
        else:
            red = 255
            green = int(health_percent * 2 * 255)
        health_color = (red, green, 0)
        pygame.draw.rect(self.screen, DARK_GREY, (x, y, bar_width, bar_height))
        pygame.draw.rect(self.screen, health_color, (x, y, int(bar_width * health_percent), bar_height))
        pygame.draw.rect(self.screen, WHITE, (x, y, bar_width, bar_height), 2)

    def draw_intro(self):
        self.screen.blit(self.menu_bg, (0, 0))
        if TITLE_IMG:
            scaled_title = pygame.transform.scale(TITLE_IMG, (TITLE_IMG.get_width() * 2, TITLE_IMG.get_height() * 2))
            self.screen.blit(scaled_title, (WINDOW_WIDTH // 2 - scaled_title.get_width() // 2, 20))
        title_txt = pygame.font.SysFont('Comic Sans MS', 60, bold=True).render("Dark-Snake", True, (50, 50, 50))
        self.screen.blit(title_txt, (WINDOW_WIDTH // 2 - title_txt.get_width() // 2, 100))
        for i, btn in enumerate(self.intro_buttons):
            if i == self.intro_focus:
                btn.is_hovered = True
            btn.draw(self.screen)

    def draw_game(self, *, include_hud=True):
        # 1. Raster (Hintergrund) zeichnen – unterste Ebene
        self.screen.blit(self.background, (0, 0))
        self.effect_manager.draw(self.screen, "background")
        # 2. AoE-Effekte zeichnen – liegen zwischen Raster und dynamischen Objekten
        for zone in self.aoe_zones:
            zone.draw(self.screen)
        if self.boss:
            self.boss.draw_aoe(self.screen)
        for explosion in self.explosions:
            explosion.draw(self.screen)
        self.effect_manager.draw(self.screen, "world")
        # 3. Dynamische Spielobjekte (Spielerebene) zeichnen:
        if self.portal:
            self.portal.draw(self.screen)
        for item in self.items:
            item.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        # Flammenprojektile zeichnen
        for proj in self.boss_flame_projectiles:
            proj.draw(self.screen)
        for flame in self.flame_projectiles:
            drawn = flame.draw(self.screen)
            if self.metrics.enabled and drawn:
                self.metrics.fire_drawn(flame)
        for proj in self.enemy_projectiles:
            proj.draw(self.screen)
        # Spieler (Snake) zeichnen:
        if self.player_count == 2:
            # Spieler 1 zeichnen:
            for i, (x, y) in enumerate(self.get_snake_render_positions(1)):
                if i == 0:
                    head_img = self.options_menu.get_skin_image(
                        "Heads", self.settings.get("custom_head_p1")) or SNAKE_HEAD_IMG
                    head_img = scale_sprite(head_img, (GRID_SIZE, GRID_SIZE))
                    try:
                        rotated = pygame.transform.rotate(head_img, -self.snake_direction1.value[0] * 90)
                    except Exception as e:
                        print("Fehler bei der Rotation des Spieler 1 Kopfbildes:", e)
                        rotated = head_img
                    self.screen.blit(rotated, (x, y))
                    if self.metrics.enabled:
                        self.metrics.head_drawn(1, (x, y), self.snake_direction1.value[0])
                else:
                    body_img = self.options_menu.get_skin_image(
                        "Bodies", self.settings.get("custom_body_p1")) or SNAKE_BODY_IMG
                    body_img = scale_sprite(body_img, (GRID_SIZE, GRID_SIZE))
                    self.screen.blit(body_img, (x, y))
            # Spieler 2 zeichnen:
            for i, (x, y) in enumerate(self.get_snake_render_positions(2)):
                if i == 0:
                    head_img = self.options_menu.get_skin_image(
                        "Heads", self.settings.get("custom_head_p2")) or SNAKE_HEAD_BETA
                    head_img = scale_sprite(head_img, (GRID_SIZE, GRID_SIZE))
                    try:
                        rotated = pygame.transform.rotate(head_img, -self.snake_direction2.value[0] * 90)
                    except Exception as e:
                        print("Fehler bei der Rotation des Spieler 2 Kopfbildes:", e)
                        rotated = head_img
                    self.screen.blit(rotated, (x, y))
                    if self.metrics.enabled:
                        self.metrics.head_drawn(2, (x, y), self.snake_direction2.value[0])
                else:
                    body_img = self.options_menu.get_skin_image(
                        "Bodies", self.settings.get("custom_body_p2")) or SNAKE_BODY_IMG
                    body_img = scale_sprite(body_img, (GRID_SIZE, GRID_SIZE))
                    self.screen.blit(body_img, (x, y))
        else:
            # Einzelspieler: Zeichne die Snake
            for i, (x, y) in enumerate(self.get_snake_render_positions(1)):
                if i == 0:
                    head_img = self.options_menu.get_skin_image(
                        "Heads", self.settings.get("custom_head_p1")) or SNAKE_HEAD_IMG
                    head_img = scale_sprite(head_img, (GRID_SIZE, GRID_SIZE))
                    try:
                        rotated = pygame.transform.rotate(head_img, -self.snake_direction.value[0] * 90)
                    except Exception as e:
                        print("Fehler bei der Rotation des Kopfbildes:", e)
                        rotated = head_img
                    self.screen.blit(rotated, (x, y))
                    if self.metrics.enabled:
                        self.metrics.head_drawn(1, (x, y), self.snake_direction.value[0])
                else:
                    body_img = self.options_menu.get_skin_image(
                        "Bodies", self.settings.get("custom_body_p1")) or SNAKE_BODY_IMG
                    body_img = scale_sprite(body_img, (GRID_SIZE, GRID_SIZE))
                    self.screen.blit(body_img, (x, y))

        # Weitere Elemente (Boss, Projektile, HUD, etc.) werden wie gehabt gezeichnet...
        if self.boss:
            self.boss.draw(self.screen)
        for proj in self.projectiles:
            proj_x = int(proj['pos'][0] * GRID_SIZE)
            proj_y = int(proj['pos'][1] * GRID_SIZE)
            if proj.get("from_boss", False):
                proj_img = scale_sprite(proj.get("image", PROJECTILE_IMG), (GRID_SIZE * 2, GRID_SIZE * 2))
            else:
                proj_img = scale_sprite(PROJECTILE_IMG, (int(GRID_SIZE * 1.5), int(GRID_SIZE * 1.5)))
            self.screen.blit(proj_img, (proj_x, proj_y))

        # --- DEBUG: hitbox overlay (one color per gameplay category) ---
        if self.debug_show_hitboxes:
            player_color = GREEN
            enemy_color = RED
            item_color = (0, 220, 255)
            projectile_color = ORANGE
            # snake segments
            if self.player_count == 1:
                for rect in self.get_snake_render_hitboxes(1):
                    pygame.draw.rect(self.screen, player_color, rect, 2)
            else:
                for player in (1, 2):
                    for rect in self.get_snake_render_hitboxes(player):
                        pygame.draw.rect(self.screen, player_color, rect, 2)
            # enemies
            for e in self.enemies:
                pygame.draw.rect(self.screen, enemy_color, e.get_hitbox(), 2)
            for item in self.items:
                pygame.draw.rect(self.screen, item_color, item.get_hitbox(), 2)
            # projectiles
            for proj in self.projectiles:
                px = int(proj['pos'][0] * GRID_SIZE)
                py = int(proj['pos'][1] * GRID_SIZE)
                size = GRID_SIZE * 2 if proj.get("from_boss") else int(GRID_SIZE * 1.5)
                pygame.draw.rect(self.screen, projectile_color, (px, py, size, size), 2)
            for projectile in self.flame_projectiles + self.enemy_projectiles + self.boss_flame_projectiles:
                hitbox = projectile.get_hitbox() if hasattr(projectile, "get_hitbox") else projectile.rect
                pygame.draw.rect(self.screen, projectile_color, hitbox, 2)
            # boss
            if self.boss:
                pygame.draw.rect(self.screen, enemy_color, self.boss.get_hitbox(), 3)
            # portal
            if self.portal:
                pr = self.portal.get_rect()
                pygame.draw.rect(self.screen, item_color, pr, 1)

        if include_hud:
            self.draw_hud()
        if self.dice_result is not None and time.time() <= self.dice_display_until:
            self.draw_dice_result()
    # Zeichnet das Ergebnis des Würfelwurfs in der Mitte des Bildschirms.
    def draw_dice_result(self):
        dice_rect = pygame.Rect(WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT // 2 - 50, 100, 100)
        pygame.draw.rect(self.screen, PURPLE, dice_rect, border_radius=15)
        pygame.draw.rect(self.screen, WHITE, dice_rect, 2, border_radius=15)
        res_txt = pygame.font.SysFont('Arial', 50).render(str(self.dice_result), True, WHITE)
        self.screen.blit(
            res_txt,
            (
                WINDOW_WIDTH // 2 - res_txt.get_width() // 2,
                WINDOW_HEIGHT // 2 - res_txt.get_height() // 2,
            ),
        )
        if self.dice_result == 1:
            desc = pygame.font.SysFont('Arial', 20).render("Kritischer Fehlschlag!", True, RED)
        elif self.dice_result == 20:
            desc = pygame.font.SysFont('Arial', 20).render("Kritischer Erfolg!", True, GOLDEN)
        elif self.dice_result > 15:
            desc = pygame.font.SysFont('Arial', 20).render("Großer Erfolg!", True, GREEN)
        elif self.dice_result > 10:
            desc = pygame.font.SysFont('Arial', 20).render("Erfolg", True, GREEN)
        elif self.dice_result > 5:
            desc = pygame.font.SysFont('Arial', 20).render("Kleiner Erfolg", True, WHITE)
        else:
            desc = pygame.font.SysFont('Arial', 20).render("Fehlschlag", True, RED)
        self.screen.blit(desc, (WINDOW_WIDTH // 2 - desc.get_width() // 2, WINDOW_HEIGHT // 2 + 40))



    # [KS_TAG: SPAWN_BOSS_AOE]
    def spawn_boss_aoe_zone(self, center_pos):
        radius_start = int(GRID_SIZE * 1.2)
        radius_max = int(GRID_SIZE * 2.5)
        duration = 3.0  # Sekunden
        zone = GrowingBossAOEZone(center_pos, radius_start, radius_max, duration, (255, 0, 0, 180), "damage")
        self.aoe_zones.append(zone)

    def draw_pause(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        pause_txt = pygame.font.SysFont('Arial', 50).render("PAUSE", True, WHITE)
        self.screen.blit(pause_txt, (WINDOW_WIDTH // 2 - pause_txt.get_width() // 2, 100))
        for btn in self.pause_buttons:
            btn.draw(self.screen)

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        go_txt = pygame.font.SysFont('Arial', 50).render("GAME OVER", True, RED)
        self.screen.blit(go_txt, (WINDOW_WIDTH // 2 - go_txt.get_width() // 2, 100))
        score_txt = pygame.font.SysFont('Arial', 30).render(f"Dein Score: {self.score}", True, WHITE)
        self.screen.blit(score_txt, (WINDOW_WIDTH // 2 - score_txt.get_width() // 2, 180))
        if self.leaderboard_mode:
            in_txt = pygame.font.SysFont('Arial', 30).render("Gib deinen Namen ein:", True, WHITE)
            self.screen.blit(in_txt, (WINDOW_WIDTH // 2 - in_txt.get_width() // 2, 230))
            input_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, 270, 300, 40)
            pygame.draw.rect(self.screen, DARK_GREY, input_rect)
            pygame.draw.rect(self.screen, WHITE, input_rect, 2)
            name_txt = pygame.font.SysFont('Arial', 30).render(self.name_input, True, WHITE)
            self.screen.blit(name_txt, (input_rect.x + 10, input_rect.y + 5))
            if int(time.time() * 2) % 2 == 0:
                cur_x = input_rect.x + 10 + name_txt.get_width()
                pygame.draw.line(self.screen, WHITE, (cur_x, input_rect.y + 5), (cur_x, input_rect.y + 35), 2)
        else:
            for btn in self.game_over_buttons:
                btn.draw(self.screen)

    def draw_leaderboard(self):
        self.screen.fill(DARK_GREY)
        title_txt = pygame.font.SysFont('Arial', 50).render("BESTENLISTE", True, GOLDEN)
        self.screen.blit(title_txt, (WINDOW_WIDTH // 2 - title_txt.get_width() // 2, 50))
        y_pos = 150
        if not self.leaderboard:
            none_txt = pygame.font.SysFont('Arial', 30).render("Keine Einträge vorhanden", True, WHITE)
            self.screen.blit(none_txt, (WINDOW_WIDTH // 2 - none_txt.get_width() // 2, y_pos))
        else:
            for i, (name, score) in enumerate(self.leaderboard[:10]):
                col = GOLDEN if i == 0 else ((192,192,192) if i == 1 else (205,127,50) if i == 2 else WHITE)
                entry_txt = pygame.font.SysFont('Arial', 30).render(f"{i+1}. {name}: {score}", True, col)
                self.screen.blit(entry_txt, (WINDOW_WIDTH // 2 - 150, y_pos))
                y_pos += 40
        back_btn = Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 80, 200, 60, "ZURÜCK", color=PURPLE, action=lambda: self.confirm_back_to_main())
        back_btn.draw(self.screen)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                self.level_editor.toggle()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.admin_panel.toggle()
            self.admin_panel.handle_event(event)
            self.level_editor.handle_event(event)
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mpos = pygame.mouse.get_pos()
                if back_btn.check_hover(mpos):
                    back_btn.handle_event(event)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.set_state(GameState.INTRO)

    def run_frame(self):
        start = self.metrics.stamp()
        self.handle_events()
        after_events = self.metrics.stamp()
        if (self.game_state in (GameState.GAME, GameState.BOSS_FIGHT)
                and not self.admin_panel.active and not self.level_editor.active):
            self.update()
        after_update = self.metrics.stamp()
        self.metrics.record_phase("events", start, after_events)
        self.metrics.record_phase("update", after_events, after_update)
        self.draw()

    def run(self):
        while True:
            self.run_frame()
            self.clock.tick(FPS)

    # [KS_TAG: LEVEL_EDITOR_BACKGROUND]
    def _build_default_background(self):
        """Erzeugt den normalen Hintergrund unabhängig von einer Editor-Karte."""
        surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        surf.fill((102, 51, 0))
        for x in range(0, WINDOW_WIDTH, GRID_SIZE * 2):
            for y in range(0, WINDOW_HEIGHT, GRID_SIZE * 2):
                pygame.draw.rect(surf, (153, 102, 51), (x, y, GRID_SIZE, GRID_SIZE))
        return surf

    def build_background_from_map(self):
        """
        Wandelt die Level-Karte in eine Hintergrund-Oberfläche um.
        Wird vom LevelEditor beim Simulieren verwendet.
        """
        from modules.graphics import get_tile  # Zentrale Tile-Zugriffs-Funktion
        if not hasattr(self, "level_map") or not self.level_map:
            self.level_background_surface = self.default_background_surface.copy()
            print("[DEBUG] Keine Level-Karte gesetzt – Standardhintergrund aufgebaut.")
            return self.level_background_surface

        surf = pygame.Surface((GRID_WIDTH * GRID_SIZE, GRID_HEIGHT * GRID_SIZE), pygame.SRCALPHA)
        for y, row in enumerate(self.level_map):
            for x, tile in enumerate(row):
                if tile:
                    img = get_tile(tile)
                    if img:
                        surf.blit(img, (x * GRID_SIZE, y * GRID_SIZE))
        self.level_background_surface = surf
        print("[DEBUG] Hintergrund aus Level-Karte aufgebaut.")
        return self.level_background_surface
    # [KS_TAG: BOSS_FLAME_PROJECTILE]
    def boss_shoots_flame(self):
        from modules.boss_projectiles import BossFlameProjectile
        if len(self.boss_flame_projectiles) >= MAX_BOSS_FLAMES:
            return
        if not self.boss:
            print("[DEBUG] Kein Boss vorhanden – BossFlameProjectile nicht erzeugt.")
            return

        if self.player_count == 1 and self.snake:
            target = self.snake[0]
        elif self.player_count == 2 and self.snake1:
            target = self.snake1[0]
        else:
            print("[DEBUG] Kein Ziel vorhanden – BossFlameProjectile nicht erzeugt.")
            return

        dx = target[0] - self.boss.x
        dy = target[1] - self.boss.y
        distance = max(1, (dx**2 + dy**2)**0.5)
        direction = (dx / distance, dy / distance)

        center_x = self.boss.x * GRID_SIZE + (self.boss.size * GRID_SIZE) // 2
        center_y = self.boss.y * GRID_SIZE + (self.boss.size * GRID_SIZE) // 2

        proj = BossFlameProjectile(center_x, center_y, direction)
        self.boss_flame_projectiles.append(proj)
        self.log_combat_event("projectile_fired", projectile="boss_projectile")
        print("[DEBUG] BossFlameProjectile aktiv mit Explosion bei Treffer!")
    
    def spawn_custom_projectile(self, x, y, direction, speed=6, damage=3, lifetime=180, image_name="projectiles/FlameProjectile1.png"):
        from math import atan2, degrees
        image_orig = load_image(image_name)
        angle = degrees(atan2(-direction[1], direction[0]))
        image = pygame.transform.rotate(image_orig, angle)
        rect = image.get_rect(center=(x, y))
        projectile = {
            "image": image,
            "rect": rect,
            "speed": speed,
            "dir": direction,
            "damage": damage,
            "lifetime": lifetime,
            "from_boss": False,
            "effect": "custom"
        }
        self.projectiles.append(projectile)
        print(f"[DEBUG] Benutzerdefiniertes Projektil gespawnt: {image_name}, Dmg: {damage}, Speed: {speed}")


        # ------------------------------------------------------
    # Explosion Animation Handling
    # ------------------------------------------------------
    def spawn_fire_explosion(self, center_pos):
        """Erzeugt eine Explosion an der gegebenen Pixel-Position mit 9 Frames."""
        explosion = FireExplosionAnimation(center_pos, scale_factor=3)
        self.explosions.append(explosion)
        self.effect_manager.spawn("explosion", center_pos)

class FlameProjectile:
    """
    Erweiterte Version eines Flammenprojektils mit parametrisierbaren Attributen.
    """
    def __init__(self, x, y, direction, image_name="projectiles/FlameProjectile1.png",
                 speed=PLAYER_FIREBALL_SPEED_PX_PER_TICK, damage=PLAYER_FIREBALL_DAMAGE,
                 lifetime=PLAYER_FIREBALL_LIFETIME_TICKS):
        from math import atan2, degrees

        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.image_orig = load_projectile_image(image_name)
        angle = degrees(atan2(-self.direction[1], self.direction[0]))
        self.image = pygame.transform.rotate(self.image_orig, angle)
        self.rect = self.image.get_rect(center=(x, y))
        self.previous_rect = self.rect.copy()

    def update(self):
        self.previous_rect = self.rect.copy()
        self.rect.x += self.speed * self.direction[0]
        self.rect.y += self.speed * self.direction[1]
        self.lifetime -= 1
        return self.lifetime > 0

    def get_render_rect(self):
        return self.rect.copy()

    def get_hitbox(self):
        # Union prevents a fast projectile from tunnelling between ticks.
        return self.rect.union(self.previous_rect)

    def draw(self, screen):
        return screen.blit(self.image, self.rect)


if __name__ == "__main__":
    game = Game()
    game.run()
    input("\n[Drücke Enter zum Schließen des Spiels...]")

    # [KS_TAG: ADMIN_HOOKS]
    def spawn_item_at(self, item_type, x, y):
        from modules.enums import ItemType
        from modules.items import Item
        if hasattr(self, "items"):
            self.items.append(Item(item_type, x, y))
            print("[ADMIN] Item gespawnt an", x, y)

    def create_damage_zone(self, x, y):
        from modules.aoe_zones import DamageZone
        if hasattr(self, "aoe_zones"):
            self.aoe_zones.append(DamageZone(x, y, radius=2))
            print("[ADMIN] DamageZone erzeugt")

    def create_slow_zone(self, x, y):
        from modules.aoe_zones import SlowZone
        if hasattr(self, "aoe_zones"):
            self.aoe_zones.append(SlowZone(x, y, radius=2))
            print("[ADMIN] SlowZone erzeugt")

    def spawn_explosive_projectile(self):
        from modules.special_projectiles import ExplosiveProjectile
        if hasattr(self, "projectiles"):
            x, y = self.snake.head.x, self.snake.head.y
            self.projectiles.append(ExplosiveProjectile(x, y, direction=(0, -1)))
            print("[ADMIN] Explosiver Schuss gespawnt")

    def start_boss_fight(self):
        from modules.bosses import Boss
        if not self.boss_fight_active:
            self.boss = Boss()
            self.boss_fight_active = True
            print("[ADMIN] Bossfight gestartet")

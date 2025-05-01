#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Modul: game.py
# Zweck: Hauptlogik für Dark-Snake inkl. Kollisionsprüfung, Schadensberechnung,
#        Projektil‑Schusstiming, Health-System, AoE-Effekten etc.
#

import pygame, sys, random, time, os, datetime, json
from math import sqrt, atan2, cos, sin
from pygame.math import Vector2

from modules.enums import GameState, Direction, ItemType
from config import (WINDOW_WIDTH, WINDOW_HEIGHT, GRID_SIZE, FPS, GRID_WIDTH, GRID_HEIGHT,
                    DARK_GREY, WHITE, GREEN, RED, PURPLE, ORANGE, GOLDEN, LEADERBOARD_FILE,
                    START_SPEED, MAX_SPEED, PROJECTILE_SPEED_FACTOR, AUTO_SHOOT_INTERVAL, BORDER_SIZE, UI_CONTAINER_HEIGHT)
# <-- Hier den fehlenden Import hinzufügen:
from modules.graphics import (
    load_image,                          # the helper itself
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
from modules.audio import SOUNDS, get_music_library, play_background_music, set_music_volume
from modules.ui import Button, Slider, CheckBox, Dropdown
from modules.aoe_zones import AoEZone, DamageZone, HealZone, DebuffZone, FollowZone, GrowingBossAOEZone  # [KS_TAG: BOSS_AOE]
from modules.controls import ControlsMenu
from modules.customization import CustomizationMenu
from modules.enemies import NormalEnemy
from modules.bolbu_enemy import BolbuEnemy
from modules.options_menu import OptionsMenu, ExtendedOptionsMenu
from modules.admin_panel import AdminPanel
from modules.fire_explosion import FireExplosionAnimation

# Boss-Projektil-Grafiken (zufällige Auswahl)
BOSS_PROJECTILES = []
for fname in ["Projektil2.png", "Projektil3.png", "Projektil4.png", "Projektil5.png"]:
    path = os.path.join("assets", "graphics", fname)
    try:
        img = pygame.image.load(path).convert_alpha()
        BOSS_PROJECTILES.append(img)
    except Exception as e:
        print(f"Fehler beim Laden von {fname}: {e}")

def get_random_projectile_color():
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))

def get_aoe_effect():
    effect_folder = os.path.join("assets", "graphics", "AOEEffekte")
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
    available_effects = []
    for fname in effect_files:
        path = os.path.join(effect_folder, fname)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (int(GRID_SIZE * 3), int(GRID_SIZE * 3)))
            available_effects.append(img)
    if available_effects:
        effect = random.choice(available_effects)
        print("DEBUG: Effektbild geladen:", effect)
        return effect
    print("DEBUG: Kein Effektbild gefunden im Ordner", effect_folder)
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
            folder = os.path.join("assets", "graphics", "Boss001")
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
            folder = os.path.join("assets", "graphics", "Boss002")
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
            folder = os.path.join("assets", "graphics", "Boss003")
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
            path = os.path.join("assets", "graphics", fname)
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
        if self.aoe_effect:
            elapsed = time.time() - self.aoe_effect["start_time"]
            if elapsed < self.aoe_effect["duration"]:
                scale = 1 + elapsed * ((self.aoe_effect["max_size"] / (self.size * GRID_SIZE) - 1)
                                       / self.aoe_effect["duration"])
                aoe_img = pygame.transform.scale(self.aoe_effect["image"],
                                                   (int(self.size * GRID_SIZE * scale),
                                                    int(self.size * GRID_SIZE * scale)))
                pos_x = self.x * GRID_SIZE + (self.size * GRID_SIZE - aoe_img.get_width()) // 2
                pos_y = self.y * GRID_SIZE + (self.size * GRID_SIZE - aoe_img.get_height()) // 2
                aoe_img.set_alpha(204)
                screen.blit(aoe_img, (pos_x, pos_y))
            else:
                self.aoe_effect = None

    def get_rect(self):
        rect = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE,
                           self.size * GRID_SIZE, self.size * GRID_SIZE)
        return rect

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
            path = os.path.join("assets", "graphics", fname)
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
    def __init__(self, item_type):
        self.x = random.randint(0, GRID_WIDTH - 1)
        self.y = random.randint(0, GRID_HEIGHT - 1)
        self.type = item_type
        self.activation_time = 0
        self.duration = 0

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
    def __init__(self):
        global WINDOW_WIDTH, WINDOW_HEIGHT, GRID_WIDTH, GRID_HEIGHT
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Dark-Snake")
        try:
            icon = pygame.image.load(os.path.join("assets", "graphics", "titel2.png")).convert_alpha()
            icon = pygame.transform.scale(icon, (32, 32))
            pygame.display.set_icon(icon)
        except Exception as e:
            print(f"Fehler beim Laden des Icons: {e}")
        self.clock = pygame.time.Clock()
        self.settings = {
            'initial_speed': START_SPEED,
            'fullscreen': False,
            'music_volume': 0.2,
            'sfx_volume': 2.0,
            'bg_music_volume': 0.3,
            'difficulty': 1.0,
            'field_scale': 1.0,
            'snake_design': 0,
            'custom_head_p1': None,
            'custom_body_p1': None,
            'custom_head_p2': None,
            'custom_body_p2': None,
            'projectile_speed_factor': PROJECTILE_SPEED_FACTOR,
            'auto_shoot_interval': AUTO_SHOOT_INTERVAL,  # Neuer konfigurierbarer Parameter für die Schussfrequenz
            'enemy_spawn_rate': 0.01,
            'boss_health_multiplier': 1.0
        }
        self.get_music_library = get_music_library
        play_background_music("/home/demus/Schreibtisch/complete-snake-game/assets/sounds/music/DarkSnakeMusicIndi2.mp3",
                              self.settings['bg_music_volume'])
        self.player_count = 1
        self.create_ui_elements()
        self.reset_game()
        self.current_frame_index = 0
        self.last_anim_time = time.time()
        self.last_auto_shoot = time.time()
        self.last_auto_shoot1 = time.time()
        self.last_auto_shoot2 = time.time()
        self.background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.background.fill((102, 51, 0))
        for i in range(0, WINDOW_WIDTH, GRID_SIZE * 2):
            for j in range(0, WINDOW_HEIGHT, GRID_SIZE * 2):
                pygame.draw.rect(self.background, (153, 102, 51), (i, j, GRID_SIZE, GRID_SIZE))
        self.menu_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
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
        self.respawn_invincible_until = 0
        self.level_editor = LevelEditor(self)

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
                   color=RED, action=lambda: sys.exit(), image=scale_image(PLAY_BUTTON_IMG))
        ]

    def create_additional_ui(self):
        center_x = WINDOW_WIDTH // 2
        button_width = 160
        button_height = 40
        self.pause_buttons = [
            Button(center_x - 100, WINDOW_HEIGHT // 2, button_width, button_height, "PAUSE",
                   action=lambda: self.set_state(GameState.PAUSE)),
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 80, button_width, button_height, "HAUPTMENÜ",
                   color=PURPLE, action=lambda: self.confirm_back_to_main()),
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 160, button_width, button_height, "BEENDEN",
                   color=RED, action=lambda: sys.exit())
        ]
        self.game_over_buttons = [
            Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 100, button_width, button_height, "NEUSTART",
                   action=lambda: self.reset_game()),
            Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 180, button_width, button_height, "HAUPTMENÜ",
                   color=PURPLE, action=lambda: self.confirm_back_to_main())
        ]

    def load_leaderboard(self):
        leaderboard = []
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, "r") as f:
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

    def save_settings(self):
        with open("settings.txt", "w") as f:
            for key, value in self.settings.items():
                f.write(f"{key}={value}\n")
        print("Einstellungen wurden gespeichert!")
        set_music_volume(self.settings['bg_music_volume'])

    def change_bg_music(self, selected_option):
        self.settings['bg_music_volume'] = self.music_slider.current_val
        from modules.audio import play_background_music
        play_background_music(selected_option, self.settings['bg_music_volume'])
        print(f"Hintergrundmusik geändert: {selected_option}")

    def start_game(self, players):
        self.player_count = players
        self.reset_game()
        level_path = "assets/levels/custom_level.json"
        if os.path.exists(level_path):
            try:
                with open(level_path) as f:
                    self.level_map = json.load(f)
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
        self.game_state = state
        if state == GameState.GAME:
            self.last_update_time = time.time()

    def reset_game(self):
        self.leaderboard_mode = False
        self.name_input = ""
        self.set_state(self.intro_state())
        # Respawn-Unbesiegbarkeit setzen: 3 Sekunden nach Reset
        self.respawn_invincible_until = time.time() + 3
        if self.player_count == 2:
            self.snake1 = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
            self.snake2 = [(GRID_WIDTH // 2, GRID_HEIGHT // 2 + 2)]
            self.snake_direction1 = Direction.RIGHT
            self.snake_direction2 = Direction.RIGHT
            self.next_direction1 = Direction.RIGHT
            self.next_direction2 = Direction.RIGHT
            self.last_auto_shoot1 = time.time()
            self.last_auto_shoot2 = time.time()
            self.player_health_p1 = 100
            self.player_health_p2 = 100
        else:
            self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
            self.snake_direction = Direction.RIGHT
            self.next_direction = Direction.RIGHT
            self.last_auto_shoot = time.time()
            self.player_health = 100
        self.items = []
        self.spawn_food()
        self.score = 0
        self.level = 1
        self.experience = 0
        self.exp_to_next_level = 100
        self.speed = self.settings['initial_speed']
        self.last_update_time = time.time()
        self.effects = {k: 0 for k in ('speed_boost', 'speed_reduction', 'score_boost',
                                       'invincibility', 'length_shortener', 'length_double', 'projectile_shoot')}
        self.boss = None
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

    def spawn_food(self):
        while True:
            new_item = Item(ItemType.FOOD)
            occ = (self.snake1 + self.snake2) if self.player_count == 2 else self.snake
            if (new_item.x, new_item.y) not in occ and not any(item.x == new_item.x and item.y == new_item.y for item in self.items):
                self.items.append(new_item)
                break

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

        # freie Feld­position suchen
        while True:
            new_item = Item(itype)
            occ = (self.snake1 + self.snake2) if self.player_count == 2 else self.snake
            pos_belegt = any(i.x == new_item.x and i.y == new_item.y for i in self.items)
            if (new_item.x, new_item.y) not in occ and not pos_belegt:
                self.items.append(new_item)
                break

    def level_up(self):
        self.level += 1
        self.experience -= self.exp_to_next_level
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
        self.speed = min(MAX_SPEED, self.speed + 0.5)
        self.start_boss_fight()
        self.score += 50 * self.level
        self.add_achievement(f"Level {self.level} erreicht!")

    def start_boss_fight(self):
        boss_class = random.choice([Boss, Boss2])
        self.boss = boss_class(self.level, health_multiplier=self.settings['boss_health_multiplier'])
        self.items.append(Item(ItemType.PROJECTILE_SHOOT))
        self.add_achievement(self.boss.announcement)
        self.game_state = GameState.BOSS_FIGHT

    def add_achievement(self, message):
        self.achievement_messages.append((message, time.time() + 10))

    def activate_portal(self, event):
        self.portal_effect_active = True
        self.portal_effect_end = time.time() + 60
        self.portal_spawn_cooldown = time.time() + 300
        self.portal_effect_type = event
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
            self.add_achievement("Teleport!")
        elif event == "boss":
            self.start_boss_fight()
            for _ in range(3):
                self.spawn_new_item()
            self.add_achievement("Boss-Portal!")
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
            proj_rect = pygame.Rect(new_x * GRID_SIZE, new_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if self.boss and (not proj.get("from_boss", False)) and self.boss.get_rect().colliderect(proj_rect):
                self.boss.health -= 10
                if self.boss.health <= 0:
                    self.boss = None
                    self.game_state = GameState.GAME
                    self.boss_spawn_timer = current_time + 60 + random.randint(0,30)
                    self.score += 100 * self.level
                    self.add_achievement("Boss besiegt! Boss Down Easy Going !!")
                    self.effects['boss_loot'] = current_time + 10
                continue
            if not proj.get("from_boss", False):
                size = GRID_SIZE // 2
            else:
                size = int(GRID_SIZE * proj.get("scale", 2))
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                continue
            proj_rect = pygame.Rect(new_x * GRID_SIZE, new_y * GRID_SIZE, size, size)
            target = self.snake1[0] if self.player_count == 2 and self.snake1 else (self.snake[0] if self.snake else None)
            if target:
                head_rect = pygame.Rect(target[0] * GRID_SIZE, target[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if head_rect.colliderect(proj_rect) and not proj.get("from_boss", False):
                    continue
            new_proj.append(proj)
        self.projectiles = new_proj

    def check_boss_collision(self, snake_head):
        if self.boss:
            boss_rect = self.boss.get_rect()
            head_x = snake_head[0] * GRID_SIZE + GRID_SIZE // 2
            head_y = snake_head[1] * GRID_SIZE + GRID_SIZE // 2
            return boss_rect.collidepoint(head_x, head_y)
        return False

    def auto_shoot_for_head(self, head, current_direction):
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
        proj = {'pos': (head[0], head[1]), 'dir': (dir_x, dir_y), "effect": "damage"}
        self.projectiles.append(proj)
        for _ in range(self.extra_auto_shots):
            deviation = random.uniform(-0.3, 0.3)
            proj_extra = {'pos': (head[0], head[1]),
                          'dir': (dir_x + deviation, dir_y + deviation),
                          "effect": "damage"}
            self.projectiles.append(proj_extra)

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
        current_time = time.time()
        # === [KS_FIX: PORTAL VISUAL RESTORE] ===
        if self.portal_effect_active and time.time() >= self.portal_effect_end:
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
            if random.random() < 0.002:
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
                self.enemy_projectiles.extend(enemy.projectiles)

        # AoE‑Zonen zeichnen (wird später noch gebraucht)
        for zone in self.aoe_zones:
            zone.draw(self.screen)
        for explosion in self.explosions:
            explosion.draw(self.screen)

        # ───────────────────────── 3) Kollisions­prüfungen ───────────────────────────
            # --- Sichere Kollisionsprüfung für klassische Projektile ---
        for enemy in self.enemies[:]:
            enemy_rect = enemy.get_rect()
            enemy_rect.x += (GRID_SIZE - enemy_rect.width) // 2
            enemy_rect.y += (GRID_SIZE - enemy_rect.height) // 2
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
            enemy_rect = enemy.get_rect()
            enemy_rect.x += (GRID_SIZE - enemy_rect.width) // 2
            enemy_rect.y += (GRID_SIZE - enemy_rect.height) // 2
            continue

            for proj in self.projectiles:
                proj_rect = pygame.Rect(
                    proj["pos"][0] * GRID_SIZE,
                    proj["pos"][1] * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE,
                )

                if enemy_rect.colliderect(proj_rect):
                    enemy.health -= 1
                    if enemy.health <= 0 and enemy in self.enemies:
                        self.enemies.remove(enemy)
                        self.score += 20
                        self.add_achievement("!")
                    if SOUNDS.get("gegner"):
                        SOUNDS["gegner"].play()
                    # Erstes Mal ein Portal spawnen?
                    if self.portal is None and time.time() >= self.portal_spawn_cooldown:
                        self.portal = Portal()
                    break

        # ---------- 3a)  **FlameProjectile**  ----------
        for flame in self.flame_projectiles[:]:
            # → Boss treffen
            if self.boss:
                boss_rect = self.boss.get_rect().inflate(-10, -10)
                if flame.rect.colliderect(boss_rect):
                    self.boss.health -= flame.damage
                    self.spawn_fire_explosion(flame.rect.center)
                    self.flame_projectiles.remove(flame)
                    break  # <-- korrekt beendet

            # → normalen Gegner treffen
            for enemy in self.enemies[:]:
                enemy_rect = enemy.get_rect()
                enemy_rect.x += (GRID_SIZE - enemy_rect.width) // 2
                enemy_rect.y += (GRID_SIZE - enemy_rect.height) // 2

                if time.time() - getattr(enemy, 'spawn_time', 0) < 2:
                    continue

                if flame.rect.colliderect(enemy_rect):
                    enemy.health -= flame.damage
                    self.spawn_fire_explosion(flame.rect.center)
                    if enemy.health <= 0:
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                        self.score += 20
                        self.add_achievement("Enemy roasted!")
                    if flame in self.flame_projectiles:
                        self.flame_projectiles.remove(flame)
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
            if self.player_count == 1 and self.snake:
                head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if proj.collides_with(head_rect):
                    print("[DEBUG] BossFlameProjectile trifft Spieler 1!")
                    self.spawn_fire_explosion(proj.rect.center)
                    self.player_health -= proj.damage
                    self.boss_flame_projectiles.remove(proj)
            elif self.player_count == 2:
                for snake, attr in [(self.snake1, 'player_health_p1'), (self.snake2, 'player_health_p2')]:
                    if snake:
                        head_rect = pygame.Rect(snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                        if proj.collides_with(head_rect):
                            print(f"[DEBUG] BossFlameProjectile trifft {attr}!")
                            self.spawn_fire_explosion(proj.rect.center)
                            current = getattr(self, attr)
                            setattr(self, attr, current - proj.damage)
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
                enemy_rect = enemy.get_rect()
                enemy_rect.x += (GRID_SIZE - enemy_rect.width) // 2
                enemy_rect.y += (GRID_SIZE - enemy_rect.height) // 2
                if not invincible and head_rect.colliderect(enemy_rect):
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
                    if not invincible and any(
                        head_rect.colliderect(pygame.Rect(seg[0] * GRID_SIZE,
                                                          seg[1] * GRID_SIZE,
                                                          GRID_SIZE, GRID_SIZE))
                        for seg in self.snake[1:]
                    ):
                        self.handle_self_collision()
                    else:
                        for enemy in self.enemies:
                            enemy_rect = enemy.get_rect()
                            enemy_rect.x += (GRID_SIZE - enemy_rect.width) // 2
                            enemy_rect.y += (GRID_SIZE - enemy_rect.height) // 2
                            if not invincible and head_rect.colliderect(enemy_rect):
                                current_health = getattr(self, health_attr)
                                current_health -= 10
                                setattr(self, health_attr, current_health)
                                if current_health <= 0:
                                    self.handle_death()
                                break
        for proj in self.projectiles:
            if proj.get("from_boss", False):
                if self.player_count == 1 and self.snake:
                    head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE,
                                            self.snake[0][1] * GRID_SIZE,
                                            GRID_SIZE, GRID_SIZE)
                    proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE,
                                            proj['pos'][1] * GRID_SIZE,
                                            GRID_SIZE, GRID_SIZE)
                    if not invincible and head_rect.colliderect(proj_rect):
                        self.player_health -= 10
                        if self.player_health <= 0:
                            self.handle_death()
                elif self.player_count == 2:
                    for snake, health_attr in [(self.snake1, 'player_health_p1'),
                                                 (self.snake2, 'player_health_p2')]:
                        if snake:
                            head_rect = pygame.Rect(snake[0][0] * GRID_SIZE,
                                                    snake[0][1] * GRID_SIZE,
                                                    GRID_SIZE, GRID_SIZE)
                            proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE,
                                                    proj['pos'][1] * GRID_SIZE,
                                                    GRID_SIZE, GRID_SIZE)
                            if not invincible and head_rect.colliderect(proj_rect):
                                current_health = getattr(self, health_attr)
                                current_health -= 10
                                setattr(self, health_attr, current_health)
                                if current_health <= 0:
                                    self.handle_death()
                                break
        for proj in self.projectiles:
            if proj.get("from_boss", False):
                if self.player_count == 1 and self.snake:
                    head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if not invincible and head_rect.colliderect(proj_rect):
                        self.player_health -= 10
                        if self.player_health <= 0:
                            self.handle_death()
                elif self.player_count == 2:
                    for snake, health_attr in [(self.snake1, 'player_health_p1'), (self.snake2, 'player_health_p2')]:
                        if snake:
                            head_rect = pygame.Rect(snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            if not invincible and head_rect.colliderect(proj_rect):
                                current_health = getattr(self, health_attr)
                                current_health -= 10
                                setattr(self, health_attr, current_health)
                                if current_health <= 0:
                                    self.handle_death()
        self.update_projectiles()
        if self.player_count == 1:
            self.draw_health_bar()
        elif self.player_count == 2:
            draw_health_bar_two(self)
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
            self.last_update_time = current_time
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
                    if new_head1 in self.snake1[1:]:
                        if not invincible:
                            self.handle_death()
                            return
                    self.snake1.insert(0, new_head1)
                    for i, item in enumerate(self.items[:]):
                        if new_head1[0] == item.x and new_head1[1] == item.y:
                            self.handle_item_pickup(item)
                            self.items.pop(i)
                            break
                    else:
                        self.snake1.pop()
                if self.snake2:
                    head2 = self.snake2[0]
                    self.snake_direction2 = self.next_direction2 if hasattr(self, 'next_direction2') else Direction.RIGHT
                    new_head2 = ((head2[0] + self.snake_direction2.value[0]) % GRID_WIDTH,
                                 (head2[1] + self.snake_direction2.value[1]) % GRID_HEIGHT)
                    if new_head2 in self.snake2[1:]:
                        if not invincible:
                            self.handle_death()
                            return
                    self.snake2.insert(0, new_head2)
                    for i, item in enumerate(self.items[:]):
                        if new_head2[0] == item.x and new_head2[1] == item.y:
                            self.handle_item_pickup(item)
                            self.items.pop(i)
                            break
                    else:
                        self.snake2.pop()
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
                    if new_head in self.snake[:-1]:
                        if not invincible:
                            self.handle_death()
                            return
                    self.snake.insert(0, new_head)
                    for i, item in enumerate(self.items[:]):
                        if new_head[0] == item.x and new_head[1] == item.y:
                            self.handle_item_pickup(item)
                            self.items.pop(i)
                            break
                    else:
                        self.snake.pop()
            if self.boss:
                if current_time - self.boss.spawn_time >= 3:
                    target = self.snake[0] if self.player_count == 1 and self.snake else (self.snake1[0] if self.player_count == 2 and self.snake1 else None)
                    if target and self.check_boss_collision(target) and not invincible:
                        if SOUNDS.get("damage"):
                            SOUNDS["damage"].play()
                        self.handle_death()
                    else:
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
                            if target and not invincible:
                                dx = 1 if target[0] > self.boss.x else -1 if target[0] < self.boss.x else 0
                                dy = 1 if target[1] > self.boss.y else -1 if target[1] < self.boss.y else 0
                                boss_proj_img = random.choice(BOSS_PROJECTILES) if BOSS_PROJECTILES else PROJECTILE_IMG
                                proj = {'pos': (self.boss.x, self.boss.y),
                                        'dir': (dx * self.settings['projectile_speed_factor'], dy * self.settings['projectile_speed_factor']),
                                        "effect": "damage",
                                        "from_boss": True,
                                        "image": boss_proj_img,
                                        "scale": self.boss.size}
                                self.projectiles.append(proj)
            if random.random() < 0.005 * self.settings['difficulty'] and len(self.items) < 5:
                self.spawn_new_item()
            self.update_projectiles()
        for proj in self.projectiles:
            if proj.get("from_boss", False):
                if self.player_count == 1 and self.snake:
                    head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if head_rect.colliderect(proj_rect) and not invincible:
                        if SOUNDS.get("damage"):
                            SOUNDS["damage"].play()
                        self.handle_death()
                elif self.player_count == 2:
                    for snake, health_attr in [(self.snake1, 'player_health_p1'), (self.snake2, 'player_health_p2')]:
                        if snake:
                            head_rect = pygame.Rect(snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            if head_rect.colliderect(proj_rect) and not invincible:
                                if SOUNDS.get("damage"):
                                    SOUNDS["damage"].play()
                                self.handle_death()
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
            self.handle_item_pickup(Item(random.choice(list(ItemType)[:-1])))
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
            if self.boss is not None:
                if current_time - self.last_boss_effect_time >= self.boss_effect_cooldown:
                    dmg = 5 * self.level
                    self.boss.health -= dmg
                    self.last_boss_effect_time = current_time
                    if SOUNDS.get("powerup"):
                        SOUNDS["powerup"].play()
                    self.score += 100
        
        elif item.type == ItemType.SPAWN_BOLBU:
            print('[DEBUG] SPAWN_BOLBU Item aufgenommen')
            from modules.bolbu_enemy import BolbuEnemy
            spawn_count = random.randint(1,3)
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
            self.respawn_invincible_until = time.time() + 3
        else:
            # Falls keine Leben mehr vorhanden sind, gehe auf Game Over
            self.game_state = GameState.GAME_OVER
            self.game_over_time = time.time()
        if len(self.leaderboard) < 10 or self.score > self.leaderboard[-1][1]:
            self.leaderboard_mode = True

    def handle_death(self):
        if self.player_count == 1:
            if self.player_health > 0:
                return
        elif self.player_count == 2:
            if self.player_health_p1 > 0 and self.player_health_p2 > 0:
                return
        if SOUNDS.get("gameover"):
            SOUNDS["gameover"].play()
        self.lives -= 1
        if self.lives <= 0:
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
            self.respawn_invincible_until = time.time() + 3

    def handle_events(self):
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
                self.level_editor.toggle()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.admin_panel.toggle()
            self.admin_panel.handle_event(event)
            self.level_editor.handle_event(event)
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.game_state not in (GameState.GAME, GameState.BOSS_FIGHT):
                    self.set_state(self.intro_state())
            if self.game_state == GameState.SETTINGS:
                self.options_menu.handle_event(event)
            elif self.game_state == GameState.CONTROLS:
                self.controls_menu.handle_event(event)
            elif self.game_state == GameState.CUSTOMIZATION:
                self.custom_menu.handle_event(event)
            elif self.game_state == GameState.INTRO:
                for btn in self.intro_buttons:
                    btn.check_hover(pygame.mouse.get_pos())
                    btn.handle_event(event)
            elif self.game_state == GameState.PAUSE:
                for btn in self.pause_buttons:
                    btn.check_hover(pygame.mouse.get_pos())
                    btn.handle_event(event)
            elif self.game_state == GameState.GAME_OVER:
                if self.leaderboard_mode:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_BACKSPACE:
                            self.name_input = self.name_input[:-1]
                        elif event.key == pygame.K_RETURN:
                            with open(LEADERBOARD_FILE, "a") as f:
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
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        self.set_state(GameState.PAUSE)
                    elif event.key in (pygame.K_SPACE, pygame.K_PLUS, pygame.K_KP_PLUS):
                        # Spieler 1: SPACE, Spieler 2: PLUS oder CONTROLLER
                        if self.player_count == 1:
                            if self.fireball_cooldown_p1 <= 0:
                                head = self.snake[0]
                                direction = self.snake_direction
                                head_px = head[0] * GRID_SIZE
                                head_py = head[1] * GRID_SIZE
                                flame = FlameProjectile(head_px, head_py, direction.value)
                                self.flame_projectiles.append(flame)
                                self.fireball_cooldown_p1 = FPS * 2  # 2 Sekunden
                        else:
                            if event.key == pygame.K_SPACE:  # Spieler 1 schießt mit SPACE
                                if self.fireball_cooldown_p1 <= 0:
                                    head = self.snake1[0]
                                    direction = self.snake_direction1
                                    head_px = head[0] * GRID_SIZE
                                    head_py = head[1] * GRID_SIZE
                                    flame = FlameProjectile(head_px, head_py, direction.value)
                                    self.flame_projectiles.append(flame)
                                    self.fireball_cooldown_p1 = FPS * 2
                            elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS):  # Spieler 2 schießt mit PLUS/Controller
                                if self.fireball_cooldown_p2 <= 0:
                                    head = self.snake2[0]
                                    direction = self.snake_direction2
                                    head_px = head[0] * GRID_SIZE
                                    head_py = head[1] * GRID_SIZE
                                    flame = FlameProjectile(head_px, head_py, direction.value)
                                    self.flame_projectiles.append(flame)
                                    self.fireball_cooldown_p2 = FPS * 2

                    else:
                        from math import sqrt, pi
                        zone_radius = int(sqrt(0.25 * WINDOW_WIDTH * WINDOW_HEIGHT / pi))
                        if event.key == pygame.K_r:
                            from modules.aoe_zones import DamageZone
                            pos = (self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE)
                            zone = DamageZone(pos, zone_radius, 5, (255, 0, 0, 128), effect_type="damage")
                            self.aoe_zones.append(zone)
                            print("DEBUG: DamageZone erzeugt an Position:", pos)
                        elif event.key == pygame.K_t:
                            from modules.aoe_zones import DebuffZone
                            pos = (self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE)
                            zone = DebuffZone(pos, zone_radius, 6, (0, 0, 255, 128), effect_type="slow")
                            self.aoe_zones.append(zone)
                            print("DEBUG: DebuffZone erzeugt an Position:", pos)
                        elif event.key == pygame.K_z:
                            from modules.aoe_zones import HealZone
                            pos = (self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE)
                            zone = HealZone(pos, zone_radius, 8, (0, 255, 0, 128), effect_type="heal")
                            self.aoe_zones.append(zone)
                            print("DEBUG: HealZone erzeugt an Position:", pos)

                        elif event.key == pygame.K_u:
                            from modules.aoe_zones import FollowZone
                            dummy = type("Dummy", (), {})()
                            pos = (self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE) if self.player_count == 1 else (self.snake1[0][0] * GRID_SIZE, self.snake1[0][1] * GRID_SIZE)
                            from pygame.math import Vector2
                            dummy.pos = Vector2(pos)
                            dummy.health = 100
                            dummy.base_speed = 5
                            dummy.speed = 5
                            zone = FollowZone(dummy.pos, zone_radius, 10, (255, 0, 255, 128), effect_type="aura")
                            self.aoe_zones.append(zone)
                            print("DEBUG: FollowZone (Aura) erzeugt an Position:", pos)
                        elif event.key == pygame.K_i:
                            from modules.aoe_zones import AoEZone, get_aoe_effect
                            pos = (self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE) if self.player_count == 1 else (self.snake1[0][0] * GRID_SIZE, self.snake1[0][1] * GRID_SIZE)
                            effect_img = get_aoe_effect()
                            if effect_img is None:
                                print("DEBUG: SpecialZone nicht erzeugt, da KEIN Effektbild gefunden wurde!")
                            else:
                                zone = AoEZone(pos, zone_radius, 7, (255, 255, 255, 128), effect_type="special")
                                zone.image = effect_img
                                self.aoe_zones.append(zone)
                                print("DEBUG: SpecialZone mit Effektbild erzeugt an Position:", pos)
                        elif event.key == pygame.K_o:
                            from modules.aoe_zones import AoEZone, get_aoe_effect
                            pos = (self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE) if self.player_count == 1 else (self.snake1[0][0] * GRID_SIZE, self.snake1[0][1] * GRID_SIZE)
                            zone = AoEZone(pos, zone_radius, 7, (200, 200, 200, 128), effect_type="extra")
                            zone.image = get_aoe_effect()
                            self.aoe_zones.append(zone)
                            if zone.image is None:
                                print("DEBUG: ExtraZone erzeugt, aber KEIN Effektbild gefunden!")
                            else:
                                print("DEBUG: ExtraZone mit Effektbild erzeugt an Position:", pos)
                        elif event.unicode == "ü":
                            from modules.aoe_zones import BackgroundEffectZone
                            try:
                                bg_image = pygame.image.load("assets/graphics/AOEEffekte/Backround0021.png").convert_alpha()
                            except Exception as e:
                                print(f"DEBUG: Fehler beim Laden des Hintergrundbildes: {e}")
                                bg_image = None
                            if bg_image:
                                zone = BackgroundEffectZone(bg_image, 7)
                                self.aoe_zones.insert(0, zone)
                                print("DEBUG: BackgroundEffectZone (Hintergrund-Effekt) erzeugt!")
                        if self.player_count == 1:
                            if event.key in (pygame.K_UP, pygame.K_w) and self.snake_direction != Direction.DOWN:
                                self.next_direction = Direction.UP
                            elif event.key in (pygame.K_DOWN, pygame.K_s) and self.snake_direction != Direction.UP:
                                self.next_direction = Direction.DOWN
                            elif event.key in (pygame.K_LEFT, pygame.K_a) and self.snake_direction != Direction.RIGHT:
                                self.next_direction = Direction.LEFT
                            elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.snake_direction != Direction.LEFT:
                                self.next_direction = Direction.RIGHT
                        elif self.player_count == 2:
                            if event.key == pygame.K_w and self.snake_direction1 != Direction.DOWN:
                                self.next_direction1 = Direction.UP
                            elif event.key == pygame.K_s and self.snake_direction1 != Direction.UP:
                                self.next_direction1 = Direction.DOWN
                            elif event.key == pygame.K_a and self.snake_direction1 != Direction.RIGHT:
                                self.next_direction1 = Direction.LEFT
                            elif event.key == pygame.K_d and self.snake_direction1 != Direction.LEFT:
                                self.next_direction1 = Direction.RIGHT
                            if event.key == pygame.K_UP and self.snake_direction2 != Direction.DOWN:
                                self.next_direction2 = Direction.UP
                            elif event.key == pygame.K_DOWN and self.snake_direction2 != Direction.UP:
                                self.next_direction2 = Direction.DOWN
                            elif event.key == pygame.K_LEFT and self.snake_direction2 != Direction.RIGHT:
                                self.next_direction2 = Direction.LEFT
                            elif event.key == pygame.K_RIGHT and self.snake_direction2 != Direction.LEFT:
                                self.next_direction2 = Direction.RIGHT

    def draw(self):
        if self.level_editor.active:
            self.level_editor.draw(self.screen)
            pygame.display.update()
            return
        if self.game_state == GameState.INTRO:
            self.draw_intro()
        elif self.game_state == GameState.CONTROLS:
            self.controls_menu.draw(self.screen)
        elif self.game_state == GameState.CUSTOMIZATION:
            self.custom_menu.draw(self.screen)
        elif self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
            self.draw_game()
        elif self.game_state == GameState.PAUSE:
            self.draw_game()
            self.draw_pause()
        elif self.game_state == GameState.GAME_OVER:
            self.draw_game()
            self.draw_game_over()
        elif self.game_state == GameState.SETTINGS:
            self.options_menu.draw(self.screen)
        elif self.game_state == GameState.LEADERBOARD:
            self.draw_leaderboard()
        if self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
            if self.boss_spawn_timer > time.time():
                cooldown = int(self.boss_spawn_timer - time.time())
                cd_txt = pygame.font.SysFont('Arial', 16, bold=True).render(f"Boss spawn in: {cooldown}s", True, ORANGE)
                self.screen.blit(cd_txt, (10, WINDOW_HEIGHT - 30))
        self.draw_hud()
        self.achievement_manager.draw_achievements(self.screen)
        self.achievement_manager.draw_portal_event(self.screen)
        self.admin_panel.draw(self.screen)
        pygame.display.update()

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
        for btn in self.intro_buttons:
            btn.draw(self.screen)

    def draw_game(self):
        # 1. Raster (Hintergrund) zeichnen – unterste Ebene
        self.screen.blit(self.background, (0, 0))
        # 2. AoE-Effekte zeichnen – liegen zwischen Raster und dynamischen Objekten
        for zone in self.aoe_zones:
            zone.draw(self.screen)
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
            flame.draw(self.screen)
        for proj in self.enemy_projectiles:
            proj.draw(self.screen)
        for explosion in self.explosions:
            explosion.draw(self.screen)
        # Spieler (Snake) zeichnen:
        if self.player_count == 2:
            # Spieler 1 zeichnen:
            for i, seg in enumerate(self.snake1):
                x = seg[0] * GRID_SIZE
                y = seg[1] * GRID_SIZE
                if i == 0:
                    head_file = self.settings.get('custom_head_p1')
                    if head_file:
                        head_img = load_image(head_file)
                        if head_img is None:
                            head_img = SNAKE_HEAD_IMG
                    else:
                        head_img = SNAKE_HEAD_IMG
                    head_img = pygame.transform.scale(head_img, (GRID_SIZE, GRID_SIZE))
                    try:
                        rotated = pygame.transform.rotate(head_img, -self.snake_direction1.value[0] * 90)
                    except Exception as e:
                        print("Fehler bei der Rotation des Spieler 1 Kopfbildes:", e)
                        rotated = head_img
                    self.screen.blit(rotated, (x, y))
                else:
                    body_file = self.settings.get('custom_body_p1')
                    if body_file:
                        body_img = load_image(body_file)
                        if body_img is None:
                            body_img = SNAKE_BODY_IMG
                    else:
                        body_img = SNAKE_BODY_IMG
                    body_img = pygame.transform.scale(body_img, (GRID_SIZE, GRID_SIZE))
                    self.screen.blit(body_img, (x, y))
            # Spieler 2 zeichnen:
            for i, seg in enumerate(self.snake2):
                x = seg[0] * GRID_SIZE
                y = seg[1] * GRID_SIZE
                if i == 0:
                    head_file = self.settings.get('custom_head_p2')
                    if head_file:
                        head_img = load_image(head_file)
                        if head_img is None:
                            head_img = SNAKE_HEAD_BETA
                    else:
                        head_img = SNAKE_HEAD_BETA
                    head_img = pygame.transform.scale(head_img, (GRID_SIZE, GRID_SIZE))
                    try:
                        rotated = pygame.transform.rotate(head_img, -self.snake_direction2.value[0] * 90)
                    except Exception as e:
                        print("Fehler bei der Rotation des Spieler 2 Kopfbildes:", e)
                        rotated = head_img
                    self.screen.blit(rotated, (x, y))
                else:
                    body_file = self.settings.get('custom_body_p2')
                    if body_file:
                        body_img = load_image(body_file)
                        if body_img is None:
                            body_img = SNAKE_BODY_IMG
                    else:
                        body_img = SNAKE_BODY_IMG
                    body_img = pygame.transform.scale(body_img, (GRID_SIZE, GRID_SIZE))
                    self.screen.blit(body_img, (x, y))
        else:
            # Einzelspieler: Zeichne die Snake
            for i, seg in enumerate(self.snake):
                x = seg[0] * GRID_SIZE
                y = seg[1] * GRID_SIZE
                if i == 0:
                    head_file = self.settings.get('custom_head_p1')
                    if head_file:
                        head_img = load_image(head_file)
                        if head_img is None:
                            head_img = SNAKE_HEAD_IMG
                    else:
                        head_img = SNAKE_HEAD_IMG
                    head_img = pygame.transform.scale(head_img, (GRID_SIZE, GRID_SIZE))
                    try:
                        rotated = pygame.transform.rotate(head_img, -self.snake_direction.value[0] * 90)
                    except Exception as e:
                        print("Fehler bei der Rotation des Kopfbildes:", e)
                        rotated = head_img
                    self.screen.blit(rotated, (x, y))
                else:
                    body_file = self.settings.get('custom_body_p1')
                    if body_file:
                        body_img = load_image(body_file)
                        if body_img is None:
                            body_img = SNAKE_BODY_IMG
                    else:
                        body_img = SNAKE_BODY_IMG
                    body_img = pygame.transform.scale(body_img, (GRID_SIZE, GRID_SIZE))
                    self.screen.blit(body_img, (x, y))

        # Weitere Elemente (Boss, Projektile, HUD, etc.) werden wie gehabt gezeichnet...
        if self.boss:
            self.boss.draw(self.screen)
        for proj in self.projectiles:
            proj_x = int(proj['pos'][0] * GRID_SIZE)
            proj_y = int(proj['pos'][1] * GRID_SIZE)
            if proj.get("from_boss", False):
                proj_img = pygame.transform.scale(proj.get("image", PROJECTILE_IMG),
                                                  (GRID_SIZE * 2, GRID_SIZE * 2))
            else:
                proj_img = pygame.transform.scale(PROJECTILE_IMG, (int(GRID_SIZE * 1.5), int(GRID_SIZE * 1.5)))
            self.screen.blit(proj_img, (proj_x, proj_y))

        # --- DEBUG: hitbox overlay ---
        if self.debug_show_hitboxes:
            color = (255, 0, 255)
            # snake segments
            if self.player_count == 1:
                for x, y in self.snake:
                    pygame.draw.rect(self.screen, color, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1)
            else:
                for x, y in self.snake1 + self.snake2:
                    pygame.draw.rect(self.screen, color, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 1)
            # enemies
            for e in self.enemies:
                r = e.get_rect()
                r.x += (GRID_SIZE - r.width) // 2
                r.y += (GRID_SIZE - r.height) // 2
                pygame.draw.rect(self.screen, color, r, 1)
            # projectiles
            for proj in self.projectiles:
                px = int(proj['pos'][0] * GRID_SIZE)
                py = int(proj['pos'][1] * GRID_SIZE)
                size = GRID_SIZE * 2 if proj.get("from_boss") else int(GRID_SIZE * 1.5)
                pygame.draw.rect(self.screen, color, (px, py, size, size), 1)
            # boss
            if self.boss:
                br = self.boss.get_rect()
                pygame.draw.rect(self.screen, color, br, 1)
            # portal
            if self.portal:
                pr = self.portal.get_rect()
                pygame.draw.rect(self.screen, color, pr, 1)

        # [KS_TAG: DEBUG_HITBOX_DRAW]
        if self.debug_show_hitboxes:
            for enemy in self.enemies:
                pygame.draw.rect(self.screen, RED, enemy.get_rect(), 2)
            if self.boss:
                pygame.draw.rect(self.screen, RED, self.boss.get_rect(), 2)
            for item in self.items:
                pygame.draw.rect(self.screen, RED,
                    pygame.Rect(item.x * GRID_SIZE, item.y * GRID_SIZE, GRID_SIZE, GRID_SIZE), 2)
            for proj in self.projectiles:
                x = int(proj['pos'][0] * GRID_SIZE)
                y = int(proj['pos'][1] * GRID_SIZE)
                pygame.draw.rect(self.screen, ORANGE, pygame.Rect(x, y, GRID_SIZE, GRID_SIZE), 2)
            if self.player_count == 2:
                for seg in self.snake1 + self.snake2:
                    pygame.draw.rect(self.screen, GREEN,
                        pygame.Rect(seg[0] * GRID_SIZE, seg[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE), 2)
            else:
                for seg in self.snake:
                    pygame.draw.rect(self.screen, GREEN,
                        pygame.Rect(seg[0] * GRID_SIZE, seg[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE), 2)

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

    def run(self):
        while True:
            self.handle_events()
            if self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
                self.update()
            self.draw()
            self.clock.tick(FPS)

    # [KS_TAG: LEVEL_EDITOR_BACKGROUND]
    def build_background_from_map(self):
        """
        Wandelt die Level-Karte in eine Hintergrund-Oberfläche um.
        Wird vom LevelEditor beim Simulieren verwendet.
        """
        from modules.graphics import get_tile  # Zentrale Tile-Zugriffs-Funktion
        if not hasattr(self, "level_map") or not self.level_map:
            print("[DEBUG] Keine Level-Karte gesetzt – Hintergrund bleibt leer.")
            return

        surf = pygame.Surface((GRID_WIDTH * GRID_SIZE, GRID_HEIGHT * GRID_SIZE), pygame.SRCALPHA)
        for y, row in enumerate(self.level_map):
            for x, tile in enumerate(row):
                if tile:
                    img = get_tile(tile)
                    if img:
                        surf.blit(img, (x * GRID_SIZE, y * GRID_SIZE))
        self.level_background_surface = surf
        print("[DEBUG] Hintergrund aus Level-Karte aufgebaut.")
    # [KS_TAG: BOSS_FLAME_PROJECTILE]
    def boss_shoots_flame(self):
        from modules.boss_projectiles import BossFlameProjectile
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

class FlameProjectile:
    """
    Erweiterte Version eines Flammenprojektils mit parametrisierbaren Attributen.
    """
    def __init__(self, x, y, direction, image_name="projectiles/FlameProjectile1.png", speed=6, damage=3, lifetime=180):
        from modules.graphics import load_image
        from math import atan2, degrees

        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.image_orig = load_image(image_name)
        angle = degrees(atan2(-self.direction[1], self.direction[0]))
        self.image = pygame.transform.rotate(self.image_orig, angle)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.x += self.speed * self.direction[0]
        self.rect.y += self.speed * self.direction[1]
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)


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

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
from pathlib import Path
from tempfile import NamedTemporaryFile

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
)
from modules.editor_layout import MIN_STUDIO_SIZE
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
from modules.main_menu import FrostAgeMenu, load_frostage_background
from modules.resources import asset_path, user_data_path
from modules.roof_render import draw_roof_objects
from modules.roof_settings import RoofVisibility
from modules.studio_locale import DEFAULT_STUDIO_LANGUAGE, normalize_studio_language
from modules.customization import CustomizationMenu
from modules.enemies import NormalEnemy
from modules.boss_medusa import MedusaEyes, medusa_step
from modules.boss_personality import profile_by_key, profile_for_level, guardian_step
from modules.boss_phases import BossPhases, PHASE_COLORS, RECOVERY_SECONDS
from modules.boss_balance import boss_max_health
from modules.boss_tactics import MedusaTactics
from modules.boss_defense import IncomingShot, MedusaDefense
from modules.boss_swipe import MedusaSwipe
from modules.boss_teleport import (
    BossTeleport, choose_destination, destination_is_safe,
    world_scan_target, WORLD_SCAN_SECONDS,
    RECOVERY_SECONDS as TELEPORT_RECOVERY_SECONDS,
)
from modules.boss_teleport_visual import (
    draw_teleport_markers, draw_teleport_sprite,
    draw_world_scan, draw_aborted_teleport,
)
from modules.boss_tactics_visual import draw_medusa_volley
from modules.bolbu_enemy import BolbuEnemy
from modules.options_menu import OptionsMenu, ExtendedOptionsMenu
from modules.admin_panel import AdminPanel
from modules.fire_explosion import FireExplosionAnimation
from modules.crash_reporting import record_event
from modules.simulation_ui import SimulationMenu
from modules.effect_manager import EffectManager
from modules.frost_prototype import FrostPrototype
from modules.frame_metrics import FrameMetrics
from modules.respawn import (RespawnCountdown, FrostRespawnVisual, RESPAWN_SECONDS,
                             POST_RESPAWN_PROTECTION, preferred_spawn_cells,
                             safe_spawn_cells, shift_round_timers)
from modules.game_over_visual import DarkAbyssGameOver
from modules.death_soul import DeathSoulEvent, DeathSoulVisual, SOUL_SECONDS
from modules.death_fog import AbyssFogVisual, FINAL_DEATH_SECONDS
from modules.dice_visual import FrostDiceResultVisual
from modules.round_progress import RoundJournal, begin_round, completed_round
from modules.dev_recorder import DeveloperRecorder
from modules.dev_session import DeveloperSession
from modules.dev_vitals import VitalObserver
from modules.dev_feedback_ui import DeveloperFeedbackUI
from modules.career_ranks import CareerLedger, xp_for_round
from modules.career_ceremony import career_ceremony_for_round
from modules.skin_inventory import SkinInventory, skin_registry
from modules.projectile_config import (
    BOSS_PROJECTILE_LIFETIME_TICKS,
    MAX_BOSS_FLAMES, MAX_BOSS_GRID_PROJECTILES, MAX_ENEMY_PROJECTILES,
    MAX_PLAYER_GRID_PROJECTILES, MAX_AUTO_SHOTS_PER_HEAD,
    PLAYER_FIREBALL_COOLDOWN_SECONDS, PLAYER_FIREBALL_DAMAGE,
    PLAYER_FIREBALL_LIFETIME_TICKS, PLAYER_FIREBALL_SPEED_PX_PER_TICK,
    PLAYER_PROJECTILE_DAMAGE, PLAYER_PROJECTILE_ENEMY_DAMAGE,
    player_grid_speed_cells_per_tick,
)

ENEMY_LIMIT = {1: 12, 2: 16}
NORMAL_ENEMY_CONTACT_DAMAGE = 10
NORMAL_ENEMY_CONTACT_INTERVAL = 1.0
BOSS_BODY_DAMAGE = 10
BOSS_BODY_HIT_INTERVAL = 1.0
BOSS_SPAWN_PROTECTION = 3.0
CLASSIC_BOSS_PROJECTILE_DAMAGE = 10
SNAKE_STALL_TIMEOUT = 3.0

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
    def __init__(self, level, health_multiplier=1.0, *,
                 profile_key="medusa", boss_size=None):
        self.profile = profile_by_key(profile_key)
        self.profile_key = self.profile.key
        self.x = random.randint(5, GRID_WIDTH - 5)
        self.y = random.randint(5, GRID_HEIGHT - 5)
        self.size = boss_size if boss_size is not None else 3 + level // 2
        # Balanced for one pickup shot every ~2 s; phases have time to play.
        self.health = boss_max_health(level, health_multiplier)
        self.max_health = self.health
        self.phases = BossPhases(self.profile_key, self.max_health)
        self._phase_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.speed = 1 + level * 0.2 + random.uniform(0, 0.5)
        self.last_move = time.time()
        self._visual_from = (self.x, self.y)
        self._visual_to = (self.x, self.y)
        self._visual_step_start = self.last_move
        self.chase_speed = 0.5
        self._classic_chase_speed = self.chase_speed
        self._aoe_interval = 5.0
        self._projectile_interval = 3.0
        self.eyes = MedusaEyes(heavy=self.profile.heavy_vision)
        self.eyes.MAX_EYES = self.profile.remote_eye_limit
        self.tactics = MedusaTactics()
        self.defense = MedusaDefense()
        self.swipe = MedusaSwipe()
        self.teleport = BossTeleport(self.profile_key)
        self._boss_shot_debug = (0, 0)  # shots, genuinely threatening shots
        self.ai_preview = False
        self.facing = (1, 0)
        self.navigation_blockers = frozenset()
        self.attack_mode = "normal"
        self.spawn_time = time.time()  # Zeitpunkt des Spawns
        # Identity and artwork are linked permanently, never random.
        self.image = None
        self.frames = []
        self.current_frame = 0
        self.last_frame_time = time.time()
        profile = self.profile
        self.art_asset = profile.sprite  # inspectable fixed identity for tests/debug
        footprint_px = self.size * GRID_SIZE
        if profile.frame_folder:
            folder = asset_path("graphics", profile.frame_folder)
            for i in range(profile.frame_count):
                frame_path = os.path.join(folder, f"frame{i:04d}.png")
                try:
                    img = pygame.image.load(frame_path).convert_alpha()
                    self.frames.append(pygame.transform.scale(
                        img, (footprint_px, footprint_px),
                    ))
                except (OSError, pygame.error) as error:
                    print(f"Bossbild fehlt: {frame_path} ({error})")
            if self.frames:
                self.image = self.frames[0]
        if self.image is None:
            path = asset_path("graphics", profile.sprite)
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image = pygame.transform.scale(
                    img, (footprint_px, footprint_px),
                )
            except (OSError, pygame.error) as error:
                print(f"Bossbild fehlt: {profile.sprite} ({error})")
        if SOUNDS.get("boss"):
            SOUNDS["boss"].play()
        self.special_attack_timer = time.time() + random.randint(5, 10)
        self.next_aoe = time.time() + 5
        self.next_proj = time.time() + 3
        self.aoe_effect = None
        self.announcement = f"{self.profile.name} erscheint!"

    def set_ai_preview(self, enabled):
        """KI-Test only; resets all Medusa information on switch-off."""
        enabled = bool(enabled)
        if enabled != self.ai_preview:
            self.ai_preview = enabled
            # Boss personalities have different move/attack priorities only
            # during KI-Test; the original Classic timings remain untouched.
            self.chase_speed = (
                self.profile.movement_interval if enabled
                else self._classic_chase_speed
            )
            self._aoe_interval = (self.profile.aoe_interval if enabled else 5.0)
            self._projectile_interval = (
                self.profile.projectile_interval if enabled else 3.0
            )
            self.eyes.reset()
            self.tactics.reset()
            self.defense.reset()
            self.cancel_swipe(time.time())
            self.swipe.reset()
            self.cancel_teleport(time.time())
            self.teleport.reset()
            self._boss_shot_debug = (0, 0)
            self.phases.reset()
            if enabled:
                self.apply_phase_tuning()
            else:
                # Legacy Classic behavior and cooldowns remain unchanged.
                self.tactics.COOLDOWN_SECONDS = MedusaTactics.COOLDOWN_SECONDS
                self.defense.COOLDOWN_SECONDS = MedusaDefense.COOLDOWN_SECONDS
                self.swipe.RECHARGE_SECONDS = MedusaSwipe.RECHARGE_SECONDS
                self.eyes.EYE_COOLDOWN = MedusaEyes.EYE_COOLDOWN

    def apply_phase_tuning(self):
        """Opt-in role-specific intervals; never changes attack damage/size."""
        if not self.ai_preview:
            return
        tune = self.phases.tuning()
        self.chase_speed = max(0.24, self.profile.movement_interval * tune.move)
        self._projectile_interval = max(
            1.6, self.profile.projectile_interval * tune.projectile,
        )
        self._aoe_interval = max(2.8, self.profile.aoe_interval * tune.aoe)
        self.tactics.COOLDOWN_SECONDS = max(
            4.5, MedusaTactics.COOLDOWN_SECONDS * tune.frost,
        )
        self.defense.COOLDOWN_SECONDS = max(
            5.5, MedusaDefense.COOLDOWN_SECONDS * tune.shield,
        )
        self.swipe.RECHARGE_SECONDS = max(
            9.5, MedusaSwipe.RECHARGE_SECONDS * tune.swipe,
        )
        self.eyes.EYE_COOLDOWN = max(
            2.8, MedusaEyes.EYE_COOLDOWN * tune.eye,
        )

    def begin_swipe(self, action):
        """Commit target cell, while collision and sprite follow the same swipe."""
        self.x, self.y = action.destination
        self._visual_from = self._visual_to = (self.x, self.y)
        self._visual_step_start = action.began_at
        self.last_move = action.began_at

    def cancel_swipe(self, now):
        """On pause/editor/respawn stop a half-finished movement safely."""
        if self.swipe.active(now):
            self._visual_from = self._visual_to = (self.x, self.y)
            self._visual_step_start = now
        self.swipe.cancel()

    def cancel_teleport(self, now, *, show_abort=False):
        """Abort a mid-transition warp without leaving ghost hitboxes."""
        action = self.teleport.action
        if action is not None:
            self.x, self.y = (
                action.destination if self.teleport.landed else action.origin
            )
            self._visual_from = self._visual_to = (self.x, self.y)
            self._visual_step_start = now
            self.last_move = now
        self.teleport.cancel(now, show_abort=show_abort)

    def update(self, current_time):
        if self.ai_preview and self.teleport.scanning():
            # The guardian's world search is a full-board *warning*, not an
            # opportunity to cast projectiles, move or strike invisibly.
            self.last_move = current_time
            if self.frames:
                self.update_animation(current_time)
            return None
        if self.ai_preview and self.teleport.waiting(current_time):
            # Telegraph, sink, emergence AND recovery block every new attack,
            # movement and projectile spawn. Existing bullets keep moving.
            self.last_move = current_time
            if self.frames:
                self.update_animation(current_time)
            return None
        if self.ai_preview and self.swipe.active(current_time):
            # Never chain a normal grid step or fire a new boss attack mid-dodge.
            self.last_move = current_time
            if hasattr(self, 'frames') and self.frames:
                self.update_animation(current_time)
            return None
        if self.ai_preview and self.phases.warning_active(current_time):
            # Distinct, fair phase announcement: no movement, new AoE or
            # projectiles while the next strategy is being telegraphed.
            self.last_move = current_time
            if self.frames:
                self.update_animation(current_time)
            return None
        if current_time - self.last_move >= self.chase_speed:
            previous_visual = self._visual_position(current_time)
            self.last_move = current_time
            step = None
            if self.ai_preview and self.eyes.reading.actionable:
                movement = (
                    guardian_step
                    if self.profile.movement_style == "guard" else medusa_step
                )
                step = movement(
                    (self.x, self.y), self.size,
                    self.eyes.reading.predicted_cell,
                    self.navigation_blockers, (GRID_WIDTH, GRID_HEIGHT),
                )
            if step is None:
                if self.ai_preview and self.profile.movement_style == "guard":
                    # A guardian holds the position while it has no real sight.
                    # No arbitrary wandering away from the guarded area.
                    dx = dy = 0
                else:
                    # Classic and unsighted hunters/Medusa retain patrol.
                    dx, dy = random.choice([-1, 0, 1]), random.choice([-1, 0, 1])
            else:
                dx, dy = step
            self.x += dx
            self.y += dy
            self.x = max(0, min(self.x, GRID_WIDTH - self.size))
            self.y = max(0, min(self.y, GRID_HEIGHT - self.size))
            if (dx, dy) != (0, 0):
                self.facing = (dx, dy)
            self._visual_from = previous_visual
            self._visual_to = (self.x, self.y)
            self._visual_step_start = current_time
        if hasattr(self, 'frames') and self.frames:
            self.update_animation(current_time)
        if current_time >= self.next_aoe:
            self.next_aoe = current_time + self._aoe_interval
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
            self.next_proj = current_time + self._projectile_interval
            if current_time - self.spawn_time >= 3:
                return "boss_shoot"
        return None

    def update_animation(self, current_time):
        if current_time - self.last_frame_time > 0.1:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.last_frame_time = current_time

    def _visual_position(self, current_time):
        """Normal glide is cosmetic; Swipe D uses the same pixels as collision."""
        if self.ai_preview and self.swipe.active(current_time):
            return self.swipe.action.position(current_time)
        start = self._visual_from
        end = self._visual_to
        duration = max(0.001, self.chase_speed * 0.9)
        alpha = max(0.0, min(1.0, (current_time - self._visual_step_start) / duration))
        return (start[0] + (end[0] - start[0]) * alpha,
                start[1] + (end[1] - start[1]) * alpha)

    def draw(self, screen):
        visual_x, visual_y = self._visual_position(time.time())
        pixel_x, pixel_y = round(visual_x * GRID_SIZE), round(visual_y * GRID_SIZE)
        action = self.teleport.action if self.ai_preview else None
        if self.ai_preview and self.teleport.scanning():
            draw_world_scan(
                screen, (self.x, self.y), self.size,
                self.teleport.search_started_at, time.time(),
                GRID_SIZE, GRID_WIDTH, GRID_HEIGHT, self._phase_font,
            )
        aborted = self.teleport.abort_visual if self.ai_preview else None
        if aborted is not None:
            canceled_action, canceled_at = aborted
            if time.time() - canceled_at < .55:
                draw_aborted_teleport(
                    screen, canceled_action, canceled_at, time.time(),
                    GRID_SIZE, self.size,
                )
            else:
                self.teleport.abort_visual = None
        if action is not None:
            draw_teleport_markers(
                screen, action, time.time(), GRID_SIZE, self.size,
            )
            draw_teleport_sprite(
                screen, self.image, (pixel_x, pixel_y),
                self.size * GRID_SIZE, action, time.time(),
            )
        elif self.image:
            screen.blit(self.image, (pixel_x, pixel_y))
        else:
            pygame.draw.rect(screen, RED, (pixel_x, pixel_y,
                                           self.size * GRID_SIZE, self.size * GRID_SIZE))
        # Visible in normal play, not only in Hitbox debug: a clear, quiet
        # telegraph of the upcoming phase without swapping the fixed sprite.
        phase_now = time.time()
        if self.ai_preview and self.phases.warning_active(phase_now):
            tint = PHASE_COLORS[self.profile_key]
            outline = pygame.Rect(
                pixel_x - 8, pixel_y - 8,
                self.size * GRID_SIZE + 16, self.size * GRID_SIZE + 16,
            )
            pygame.draw.ellipse(screen, tint, outline, 3)
            next_stage = self.phases.pending_stage
            label = self._phase_font.render(
                f"{self.profile.name}: Phase {next_stage} - "
                f"{self.phases.stage_name(next_stage)}",
                True, tint,
            )
            label_x = max(0, min(
                screen.get_width() - label.get_width(),
                pixel_x + (self.size * GRID_SIZE - label.get_width()) // 2,
            ))
            label_y = max(0, pixel_y - 34)
            pygame.draw.rect(
                screen, (14, 17, 27),
                (label_x - 3, label_y - 1,
                 label.get_width() + 6, label.get_height() + 2),
                border_radius=3,
            )
            screen.blit(label, (label_x, label_y))
        # Swipe has a compact violet trail frame, distinct from the shield.
        # Two pips above the health bar show the independent charged dodges.
        if self.ai_preview:
            swipe_now = time.time()
            if self.swipe.active(swipe_now):
                pygame.draw.rect(
                    screen, (192, 133, 244),
                    (pixel_x - 3, pixel_y - 3,
                     self.size * GRID_SIZE + 6, self.size * GRID_SIZE + 6),
                    2, border_radius=4,
                )
            for slot, charged_at in enumerate(self.swipe.ready_at):
                pygame.draw.circle(
                    screen,
                    (164, 220, 255) if swipe_now >= charged_at else (85, 77, 107),
                    (pixel_x + 7 + slot * 11, pixel_y - 18), 3,
                )
        # Short-lived, one-use shield is visible even without Hitbox Debug.
        # Never modify the boss's authoritative rectangle or gameplay timing.
        if self.ai_preview and self.defense.active(time.time()):
            shield_rect = pygame.Rect(
                pixel_x - 6, pixel_y - 6,
                self.size * GRID_SIZE + 12, self.size * GRID_SIZE + 12,
            )
            pygame.draw.ellipse(screen, (124, 219, 255), shield_rect, 3)
        bar_width = self.size * GRID_SIZE
        bar_height = 5
        # Full bar is the boss's actual max HP, not a changing divisor.
        # This also makes 70% / 35% phase limits visually interpretable.
        life_ratio = max(0, min(1, self.health / max(1, self.max_health)))
        life_bar = pygame.Rect(pixel_x, pixel_y - 10,
                               int(bar_width * life_ratio), bar_height)
        pygame.draw.rect(screen, GREEN, life_bar)
        pygame.draw.rect(screen, WHITE, (pixel_x, pixel_y - 10,
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
        now = time.time()
        if self.ai_preview and self.teleport.hidden(now):
            # No invisible hitbox left at the departure tile, and no
            # surprise hitbox at the arrival tile while emerging.
            return pygame.Rect(0, 0, 0, 0)
        if self.ai_preview and self.swipe.active(now):
            sx, sy = self.swipe.action.position(now)
            return pygame.Rect(round(sx * GRID_SIZE), round(sy * GRID_SIZE),
                               self.size * GRID_SIZE, self.size * GRID_SIZE)
        return pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE,
                           self.size * GRID_SIZE, self.size * GRID_SIZE)

    def get_hitbox(self):
        """Retain full-size boss collision, and follow a live swipe exactly."""
        return self.get_render_rect()

    def get_rect(self):
        return self.get_hitbox()

    def take_damage(self):
        self.health -= 1
        if SOUNDS.get("powerup"):
            SOUNDS["powerup"].play()
        return self.health <= 0

class Boss2(Boss):
    def __init__(self, level, health_multiplier=1.0, *,
                 profile_key="medusa"):
        # Select the larger footprint BEFORE loading fixed profile artwork.
        # Otherwise the sprite and authoritative Boss2 hitbox would differ.
        super().__init__(
            level, health_multiplier,
            profile_key=profile_key, boss_size=4 + level // 2,
        )
        self.health = boss_max_health(
            level, health_multiplier, guardian=True,
        )
        self.max_health = self.health
        self.phases.max_health = self.max_health
        self.speed = 1 + level * .25 + random.uniform(0, .5)
        self.chase_speed = 0.4
        self._classic_chase_speed = self.chase_speed
        self.attack_mode = "shield"
        self.spawn_time = time.time()
        self.special_attack_timer = time.time() + random.randint(5, 10)
        self.next_aoe = time.time() + 6
        self.next_proj = time.time() + 4

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
        self._event_font = pygame.font.SysFont("Arial", 18, bold=True)

    def _draw_notice(self, surface, text, *, right=False, y=142, tint=(236, 167, 78)):
        """Keep temporary notices outside the health-bar area (y=80..100)."""
        max_text_width = max(40, min(380, surface.get_width() // 2 - 36))
        label = str(text)
        if self._event_font.size(label)[0] > max_text_width:
            while len(label) > 1 and self._event_font.size(label + "…")[0] > max_text_width:
                label = label[:-1]
            label += "…"
        rendered = self._event_font.render(label, True, tint)
        width = rendered.get_width() + 26
        height = max(30, rendered.get_height() + 10)
        x = surface.get_width() - width - 12 if right else 12
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (23, 16, 38), rect, border_radius=6)
        pygame.draw.rect(surface, (111, 81, 145), rect, 1, border_radius=6)
        pygame.draw.rect(surface, tint, (x + 5, y + 5, 3, height - 10), border_radius=1)
        surface.blit(rendered, (x + 14, y + (height - rendered.get_height()) // 2))
        return height

    def draw_achievements(self, surface):
        now = time.time()
        self.game.achievement_messages[:] = [
            (message, expires) for message, expires in self.game.achievement_messages
            if expires >= now
        ]
        y = 142
        # Newest messages first; avoid flooding the playfield after repeated hits.
        for message, _ in reversed(self.game.achievement_messages[-4:]):
            y += self._draw_notice(surface, message, y=y) + 6

    def draw_portal_event(self, surface):
        if self.game.portal_effect_active and self.game.portal_effect_type:
            self._draw_notice(
                surface, "Portal: " + str(self.game.portal_effect_type),
                right=True, y=142, tint=(218, 147, 245),
            )
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
        # Progress persists at confirmed final Game Over, not during frames.
        # Headless development simulations do not affect real player history.
        self._round_journal = RoundJournal()
        self.dev_recorder = DeveloperRecorder()
        self.dev_session = DeveloperSession()
        self._dev_vitals = VitalObserver()
        self.dev_feedback = DeveloperFeedbackUI()
        self._dev_button_rect = pygame.Rect(0, 0, 0, 0)
        self._dev_save_rect = pygame.Rect(0, 0, 0, 0)
        self._dev_save_notice_until = 0.0
        self._dev_save_success = False
        self._dev_settings_previous = {}
        self._dev_last_round_id = None
        self._dev_ui_font = pygame.font.SysFont("Segoe UI", 14, bold=True)
        self._dev_feedback_opened_at = None
        self._dev_badge_until = 0.0
        self._career_ledger = CareerLedger()
        self._skin_inventory = SkinInventory()
        self._record_completed_rounds = not headless
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
        self._hud_badge_font = pygame.font.SysFont("Arial", 15, bold=True)
        self._enemy_ai_debug_font = pygame.font.SysFont("Arial", 12, bold=True)
        self.metrics = FrameMetrics()
        self.respawn = RespawnCountdown()
        self._respawn_recent = False
        self._respawn_visual = None  # Lazy, only loads FrostAge PNG on the first respawn.
        self._game_over_visual = None  # Lazy, cached Dark Abyss backdrop + fonts.
        self._death_soul_event = None
        self._death_soul_visual = None  # Keep scaled frames cached between lives.
        self._death_fog_visual = None  # Three translucent overlays, final life only.
        self._death_soul_frozen_world = None
        self._dice_banner = None  # Lazy, one-time scaled D20 art from bundled HUD assets.
        self._dice_visual = None  # Cached FrostAge result card; old purple box is retired.
        self.effect_manager = EffectManager()
        self.frost = FrostPrototype()
        self._effect_update_time = time.monotonic()
        self.settings = {
            'initial_speed': START_SPEED,
            'fullscreen': False,
            'studio_language': DEFAULT_STUDIO_LANGUAGE,
            'sfx_volume': DEFAULT_SFX_VOLUME,
            'bg_music_volume': DEFAULT_MUSIC_VOLUME,
            'music_track': DEFAULT_MUSIC_TRACK,
            'difficulty': 1.0,
            'field_scale': 1.0,
            'studio_erase_all_layers': True,
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
        self._menu_suspended = False
        self.create_ui_elements()
        self.reset_game()
        self.current_frame_index = 0
        self.last_anim_time = time.time()
        self.last_auto_shoot = time.time()
        self.last_auto_shoot1 = time.time()
        self.last_auto_shoot2 = time.time()
        self.default_background_surface = (pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
                                           if headless else self._build_default_background())
        self.classic_level_name = None
        self._classic_level_map = None
        # Wall/Barrier cells are vision blockers; decorative PNGs are not.
        # This does not silently change the established Classic movement rules.
        self._classic_vision_blockers = frozenset()
        self._vision_blockers = frozenset()
        self._classic_roof_objects = {}
        self._classic_roof_visibility = RoofVisibility()
        self.level_map = None
        self.level_background_surface = self.default_background_surface.copy()
        self.background = self.level_background_surface
        self.last_click_time = 0
        self.double_click_interval = 0.5
        self.respawn_invincible_until = 0
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
        self.career_snapshot = None
        self.career_progress_error = None
        self.skin_inventory_snapshot = None
        self.skin_inventory_error = None
        if self._record_completed_rounds:
            self._sync_career_progress()
            # Even if career data is corrupted, disable locked skins safely.
            self._sync_skin_inventory()

    def create_ui_elements(self):
        self.main_menu = FrostAgeMenu({
            "single_player": lambda: self.start_game(1),
            "multiplayer": lambda: self.start_game(2),
            "continue": self.continue_game,
            "options": lambda: self.set_state(GameState.SETTINGS),
            "highscore": lambda: self.set_state(GameState.LEADERBOARD),
            "level_studio": self._open_level_editor,
            "controls": lambda: self.set_state(GameState.CONTROLS),
            "developer": lambda: self.set_state(GameState.SIMULATION),
            "quit": self._dev_quit,
        }, can_continue=self.can_continue, background=load_frostage_background(TITLE_IMG))

    def _open_level_editor(self):
        if self.respawn.active:
            self._tick_respawn()
        self.admin_panel.close()
        if isinstance(self.boss, Boss):
            self.boss.tactics.cancel(time.time())
            self.boss.defense.cancel()
            self.boss.cancel_swipe(time.time())
            self.boss.cancel_teleport(time.time())
            self.boss.phases.cancel_warning()
        self.level_editor.toggle()
        if self.dev_session.active:
            self.dev_session.event("studio_toggle", active=self.level_editor.active)
            self.dev_session.checkpoint("studio_toggle")

    def _set_editor_window(self, entering):
        if self.headless:
            return
        if entering:
            size = self.level_editor.layout.bounds.size
            if pygame.display.get_driver() != "dummy":
                width, height = pygame.display.get_desktop_sizes()[0]
                available = (width - 24, height - 80)
                size = tuple(min(value, max(minimum, limit)) for value, minimum, limit in
                             zip(size, MIN_STUDIO_SIZE, available))
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
            self.level_editor.resize(self.screen.get_size())
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

    def _resize_editor_window(self):
        if self.headless:
            return
        self.screen = pygame.display.get_surface()
        size = tuple(max(value, minimum) for value, minimum in zip(self.screen.get_size(), MIN_STUDIO_SIZE))
        if self.screen.get_size() != size:
            self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
        self.level_editor.resize(self.screen.get_size())

    def create_additional_ui(self):
        center_x = WINDOW_WIDTH // 2
        button_width = 160
        button_height = 40
        self.pause_buttons = [
            Button(center_x - 100, WINDOW_HEIGHT // 2, button_width, button_height, "WEITER",
                   action=self._resume_game),
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 80, button_width, button_height, "HAUPTMENÜ",
                   color=PURPLE, action=self.open_main_menu),
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 160, button_width, button_height, "BEENDEN",
                   color=RED, action=lambda: sys.exit())
        ]
        self.game_over_buttons = [
            Button(WINDOW_WIDTH // 2 - 228, 520, 212, 52, "NEUSTART",
                   action=lambda: self.start_game(self.player_count)),
            Button(WINDOW_WIDTH // 2 + 16, 520, 212, 52, "HAUPTMENÜ",
                   color=PURPLE, action=lambda: self.set_state(GameState.INTRO))
        ]
        self.leaderboard_back_button = Button(
            center_x - 100, WINDOW_HEIGHT - 80, 200, 60, "ZURÜCK", color=PURPLE,
            action=lambda: self.set_state(GameState.INTRO),
        )

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
                self.settings['studio_language'] = normalize_studio_language(self.settings['studio_language'])
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as exc:
            record_event(f"Einstellungen konnten nicht geladen werden: {exc}")

    def save_settings(self):
        saved = True
        temporary = None
        try:
            path = Path(user_data_path("settings.json"))
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                    prefix=".settings-", suffix=".tmp", delete=False) as file:
                temporary = Path(file.name)
                json.dump(self.settings, file, ensure_ascii=False, indent=2)
                file.flush()
                os.fsync(file.fileno())
            temporary.replace(path)
            temporary = None
        except (OSError, TypeError, ValueError) as exc:
            saved = False
            self.add_achievement("Einstellungen konnten nicht gespeichert werden")
            record_event(f"Einstellungen konnten nicht gespeichert werden: {exc}")
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError as exc:
                    record_event(f"Temporäre Einstellungsdatei konnte nicht entfernt werden: {exc}")
        set_music_volume(self.settings['bg_music_volume'])
        set_sound_volume(self.settings['sfx_volume'])
        if self.dev_session.active:
            changed = sorted(k for k, v in self.settings.items()
                             if self._dev_settings_previous.get(k) != v)
            self.dev_session.event("settings_saved", changed_keys=changed, success=saved)
            if not saved:
                self.dev_session.event("session_warning", code="settings_save_failed")
            if saved:
                self._dev_settings_previous = dict(self.settings)
            self.dev_session.checkpoint("settings_saved")
        return saved

    def start_game(self, players):
        self.player_count = players
        self.reset_game()
        locations = preferred_spawn_cells(players, GRID_WIDTH, GRID_HEIGHT)
        if players == 2:
            self.snake1, self.snake2 = [locations[0]], [locations[1]]
        else:
            self.snake = [locations[0]]
        self._reset_snake_interpolation()
        self.spawn_food()
        self.level_map = [row.copy() for row in self._classic_level_map] if self._classic_level_map else None
        self._vision_blockers = self._classic_vision_blockers
        self._roof_objects = self._classic_roof_objects.copy()
        self._roof_visibility = self._classic_roof_visibility
        self.background = self.build_background_from_map()
        self._round_token = begin_round(players)
        self.dev_recorder.begin_round(self._round_token, context={
            "players": players,
            "session_id": self.dev_session.session_id if self.dev_session.active else None,
            "initial_speed": self.settings["initial_speed"],
            "difficulty": self.settings["difficulty"],
            "boss_health_multiplier": self.settings["boss_health_multiplier"],
            "projectile_speed_factor": self.settings["projectile_speed_factor"],
            "auto_shoot_interval": self.settings["auto_shoot_interval"],
            "world": self.classic_level_name,
            "grid": [GRID_WIDTH, GRID_HEIGHT],
            "vision_blockers": sorted(self._vision_blockers),
        })
        self._dev_capture_vitals("round_start", checkpoint=True)
        self.dev_session.round_start(self._round_token)
        self.set_state(GameState.GAME)

    def choose_classic_background(self, name, level_map, *, roof_objects=None,
                                  roof_visibility=None, collisions=None):
        """Remember visual layers and authored line-of-sight walls for Classic.

        The physical Classic movement map is NOT changed by this sight layer.
        """
        self.classic_level_name = name
        self._classic_level_map = [row.copy() for row in level_map] if level_map is not None else None
        self._classic_vision_blockers = frozenset(
            cell for cell, kind in (collisions or {}).items()
            if kind in ("WALL", "BARRIER")
        )
        self._classic_roof_objects = dict(roof_objects or {})
        self._classic_roof_visibility = roof_visibility if roof_visibility is not None else RoofVisibility()

    def set_state(self, state):
        # Preserve respawn time when opening or leaving a pause/menu.
        if self.respawn.active:
            self._tick_respawn()
        previous = getattr(self, "game_state", None)
        was_playing = self._gameplay_active()
        if state == GameState.INTRO and previous != GameState.INTRO and not self._menu_suspended:
            self.clear_game_state()
        if state == GameState.PAUSE and previous in (GameState.GAME, GameState.BOSS_FIGHT):
            if isinstance(self.boss, Boss):
                self.boss.tactics.cancel(time.time())
                self.boss.defense.cancel()
                self.boss.cancel_swipe(time.time())
                self.boss.cancel_teleport(time.time())
                self.boss.phases.cancel_warning()
            self._paused_state = previous
            self.metrics.cancel_pending()
        self.game_state = state
        if (self.dev_session.active and previous is not None and
                previous != state):
            self.dev_session.event(
                "navigation", source=previous.name, destination=state.name,
            )
        playing = self._gameplay_active()
        if playing and not was_playing:
            self._stall_clock_sample = time.monotonic()
        elif was_playing and not playing:
            self._suspend_stall_clock()
        if state == GameState.GAME or (previous == GameState.PAUSE and state == GameState.BOSS_FIGHT):
            self.last_update_time = time.time()

    def _resume_game(self):
        self.set_state(getattr(self, "_paused_state", GameState.GAME))

    def open_main_menu(self):
        """Keep a paused Classic round available when leaving through the pause menu."""
        if self.game_state != GameState.PAUSE:
            return
        snakes = (self.snake,) if self.player_count == 1 else (self.snake1, self.snake2)
        self._menu_suspended = self.lives > 0 and all(snakes)
        self.set_state(self.intro_state())

    def can_continue(self):
        return self._menu_suspended and self.game_state == GameState.INTRO

    def continue_game(self):
        if self.can_continue():
            self._menu_suspended = False
            self.set_state(GameState.PAUSE)
            self._resume_game()

    def _toggle_admin_panel(self):
        if self.respawn.active:
            self._tick_respawn()
        if not self._menu_suspended:
            if isinstance(self.boss, Boss):
                self.boss.tactics.cancel(time.time())
                self.boss.defense.cancel()
                self.boss.cancel_swipe(time.time())
                self.boss.cancel_teleport(time.time())
                self.boss.phases.cancel_warning()
            self.admin_panel.toggle()

    def reset_game(self):
        self.dev_recorder.finish("reset")
        self._dev_vitals.reset()
        self.dev_feedback.clear()
        self._dev_preboss_asked = False
        self._dev_boss_reviews = 0
        self._dev_portal_seen = False
        self._dev_bolbu_seen = False
        self._dev_seen_items = {}
        self._dev_end_pending = False
        self.respawn.clear()
        self._respawn_recent = False
        self._menu_suspended = False
        self.frost.clear()
        self.metrics.cancel_pending()
        self._reset_snake_stalls()
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
        self._normal_enemy_contact_ready_at = {}
        self.boss_spawn_timer = time.time() + 60
        self.game_over_time = 0
        self._death_soul_event = None
        self._death_soul_frozen_world = None
        self.round_death_count = 0
        self.pause_time = 0
        self.lives = 3
        # Round statistics are real collected items / confirmed kills, not estimates.
        self.round_items_collected = 0
        self.round_enemies_defeated = 0
        self.round_bosses_defeated = 0
        # A reset is never an automatic completed run or reward.
        self._round_token = None
        self._round_recorded = False
        self.round_progress_error = None
        # The round's career XP is awarded from committed data, never per frame.
        self.round_career_xp = 0
        self.round_career_result = None
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
        # Developer-only opt-in: Classic AI remains original on every reset.
        self.enemy_ai_preview = False
        self.last_auto_shoot = time.time()
        self.extra_auto_shots = 0
        self.aoe_zones = []

    def clear_game_state(self):
        """Drop every object belonging to a round before showing a menu."""
        self.dev_recorder.finish("menu_exit")
        self.dev_feedback.clear()
        self._dev_end_pending = False
        self.respawn.clear()
        self._respawn_recent = False
        self._menu_suspended = False
        self.metrics.cancel_pending()
        self._reset_snake_stalls()
        self._death_soul_event = None
        self._death_soul_frozen_world = None
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
        self.frost.clear()
        self.portal = None
        self.portal_effect_active = False
        self.portal_effect_type = None
        self.boss = None
        self.boss_fight_active = False
        self.lives = 0
        self.player_health = self.player_health_p1 = self.player_health_p2 = 0
        self.level_map = None
        self._roof_objects = {}
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

    def _gameplay_active(self):
        return (self.game_state in (GameState.GAME, GameState.BOSS_FIGHT)
                and not self.respawn.active
                and not self.admin_panel.active and not self.level_editor.active)

    def _reset_snake_stalls(self):
        self._blocked_since = {}
        self._stall_active_time = 0.0
        self._stall_clock_sample = None

    def _advance_stall_clock(self, now):
        """Advance the shared active clock used by each player's block timer."""
        if self._stall_clock_sample is not None:
            self._stall_active_time += max(0.0, now - self._stall_clock_sample)
        self._stall_clock_sample = now

    def _suspend_stall_clock(self):
        if self._stall_clock_sample is not None:
            self._advance_stall_clock(time.monotonic())
            self._stall_clock_sample = None

    def _move_snake(self, player, snake, direction, invincible):
        """Keep every body tile solid, including during damage invulnerability.

        The only legal body overlap is the vacating tail on a move without
        growth; that tile becomes free in the very same grid step. Items,
        AoE, a respawn shield and a power-up never make body cells passable.
        """
        x, y = snake[0]
        dx, dy = direction.value
        new_head = ((x + dx) % GRID_WIDTH, (y + dy) % GRID_HEIGHT)
        item_index = next((index for index, item in enumerate(self.items)
                           if (item.x, item.y) == new_head), None)
        occupied = snake[1:-1] if item_index is None else snake[1:]
        if new_head in occupied:
            self._blocked_since.setdefault(player, self._stall_active_time)
            return False

        self._blocked_since.pop(player, None)
        snake.insert(0, new_head)
        if item_index is None:
            snake.pop()
        else:
            self.handle_item_pickup(self.items[item_index])
            self.items.pop(item_index)
            self.round_items_collected += 1
        return True

    def _advance_snakes(self, invincible):
        if self.respawn.active:
            return
        players = (("", self.snake),) if self.player_count == 1 else (
            ("1", self.snake1), ("2", self.snake2))
        for player, (suffix, snake) in enumerate(players, start=1):
            if not snake:
                continue
            if player == 1 and self.portal:
                x, y = snake[0]
                head_rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if head_rect.colliderect(self.portal.get_rect()):
                    self.activate_portal(self.portal.event)
                    self.portal_effect_active = True
                    self.portal = None
            direction = getattr(self, f"next_direction{suffix}", Direction.RIGHT)
            if self._move_snake(player, snake, direction, invincible):
                setattr(self, f"snake_direction{suffix}", direction)
                self.metrics.apply_direction(player, direction)

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
        self.dev_recorder.event("level_up", level=self.level)
        self.experience -= self.exp_to_next_level
        self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
        self.speed = min(MAX_SPEED, self.speed + 0.5)
        self.start_boss_fight()
        self.score += 50 * self.level
        self.add_achievement(f"Level {self.level} erreicht!")

    def start_boss_fight(self):
        if self.boss is not None:
            return False
        # Stable boss identity by level: Medusa → Jäger → Wächter.
        # Artwork and abilities always match the selected profile.
        profile = profile_for_level(self.level)
        boss_class = Boss2 if profile.larger_boss else Boss
        self.boss = boss_class(
            self.level,
            health_multiplier=self.settings["boss_health_multiplier"],
            profile_key=profile.key,
        )
        self.boss_fight_started_at = time.time()
        self._boss_contact_ready_at.clear()
        self._spawn_item_in_free_cell(ItemType.PROJECTILE_SHOOT)
        self.add_achievement(self.boss.announcement)
        self.game_state = GameState.BOSS_FIGHT
        self.background = self.level_background_surface
        self.boss_fight_active = True
        self.dev_recorder.event(
            "boss_spawn", boss=self.boss.profile_key, level=self.level,
            hp=self.boss.health, max_hp=self.boss.max_health,
            cell=[self.boss.x, self.boss.y], size=self.boss.size,
        )
        # Snapshot captures both player HP and shared lives BEFORE any boss damage.
        self._dev_capture_vitals("boss_entry", checkpoint=True)
        self.dev_recorder.checkpoint("boss_spawn")
        boss_center = ((self.boss.x + self.boss.size / 2) * GRID_SIZE,
                       (self.boss.y + self.boss.size / 2) * GRID_SIZE)
        self.boss.aura_effect = self.effect_manager.spawn(
            "boss_aura", boss_center, {"loop": True, "lifetime": 60.0},
        )
        record_event(f"Bosskampf gestartet: Level {self.level}")
        if (self.dev_recorder.active and not self._dev_preboss_asked
                and not self.headless):
            self._dev_preboss_asked = True
            self._dev_ask("zone_before_boss",
                          "Wie fair war die Zone bis zum ersten Boss?")
        return True

    def add_achievement(self, message):
        self.achievement_messages.append((message, time.time() + 10))

    def log_combat_event(self, event_type, **details):
        event = {"type": event_type, "time": time.time(), **details}
        self.combat_events.append(event)
        self.dev_recorder.event(event_type, **details)
        if event_type == "boss_defeated":
            self.dev_recorder.checkpoint("boss_defeated")
        record_event(event_type + (f": {details}" if details else ""))

    def _toggle_dev_recorder(self):
        """One opt-in session covers menu visits and any number of rounds."""
        if self._menu_suspended:
            return
        requested = not self.dev_recorder.enabled
        if requested:
            if self.dev_recorder.configure(True):
                self.dev_session.start()
                self._dev_settings_previous = dict(self.settings)
        else:
            if self.dev_session.active and not self.dev_session.end("disabled"):
                self._dev_save_success = False
                self._dev_save_notice_until = time.monotonic() + 3.0
                return  # Save failure: remain enabled, show red status.
            self.dev_recorder.configure(False)
        self._dev_badge_until = time.monotonic() + 2.0

    def _dev_save_session(self):
        if not self.dev_session.active:
            return False
        round_ok = (self.dev_recorder.checkpoint("manual")
                    if self.dev_recorder.active else True)
        session_ok = self.dev_session.checkpoint("manual")
        saved = round_ok and session_ok
        self._dev_save_success = saved
        self._dev_save_notice_until = time.monotonic() + 3.0
        return saved

    def _dev_mark_issue(self):
        if not self.dev_session.active:
            return
        self.dev_session.event(
            "tester_marker",
            screen="WORLD_STUDIO" if self.level_editor.active else self.game_state.name,
            level=self.level,
            boss=getattr(self.boss, "profile_key", None),
            round_id=self._round_token.get("round_id") if self._round_token else None,
        )
        self.dev_session.checkpoint("tester_marker")
        self._dev_badge_until = time.monotonic() + 3

    def _dev_mark_test_intent(self):
        """Optional F10 after a completed round. Does not alter technical end."""
        if (not self.dev_session.active or not self.dev_session.rounds
                or not self.dev_session.rounds[-1].get("finished_at")):
            return False
        latest = self.dev_session.rounds[-1]
        if latest.get("tester_intent") == "intentional_test_end":
            return True
        report_ok = True
        if self.dev_recorder.round_id == latest["round_id"]:
            report_ok = self.dev_recorder.mark_tester_intent("intentional_test_end")
        session_ok = self.dev_session.mark_round_intent("intentional_test_end")
        self._dev_save_success = report_ok and session_ok
        self._dev_save_notice_until = time.monotonic() + 3.0
        return self._dev_save_success

    def _dev_shutdown(self):
        """Best-effort close, no effect on career files or gameplay results."""
        if self.dev_recorder.active:
            self.dev_recorder.checkpoint("quit")
        if self.dev_session.active:
            self.dev_session.end("quit")

    def _dev_quit(self):
        self._dev_shutdown()
        sys.exit()

    def _dev_capture_vitals(self, source, *, checkpoint=False):
        """Telemetry only: never modify HP, lives, RNG or movement."""
        if self.dev_recorder.active:
            self._dev_vitals.observe(
                self, self.dev_recorder, source=source, checkpoint=checkpoint,
            )

    def _dev_item_state(self, now):
        """Actual runtime effects before/after pickup, not guessed item stats."""
        return {
            "score": self.score,
            "xp": self.experience,
            "speed": self.speed,
            "boss_hp": self.boss.health if self.boss is not None else None,
            "enemies": len(self.enemies),
            "effects_left_s": {
                name: round(max(0.0, until - now), 2)
                for name, until in self.effects.items() if until > now
            },
            "auto_shoot_interval": self.settings.get("auto_shoot_interval"),
        }

    def _dev_ask(self, subject, prompt, *, items=()):
        if not self.dev_recorder.enabled or self.headless:
            return
        started = self.dev_feedback.active
        if self.dev_feedback.enqueue(subject, prompt, items=items) and not started:
            self._dev_feedback_opened_at = time.time()
            self._suspend_stall_clock()
            self.metrics.cancel_pending()

    def _dev_ask_round_end(self):
        """Only relevant topics; no question for every boss phase or pickup."""
        if not self.dev_recorder.enabled or self.headless:
            return
        if not self._dev_preboss_asked:
            self._dev_ask("zone_round_end", "Wie fair war die Zone dieser Runde?")
        if self._dev_portal_seen:
            self._dev_ask("portal", "Waren Portale und ihre Warnungen verständlich?")
        if self._dev_bolbu_seen:
            self._dev_ask("enemy:bolbu", "Wie fair war der zusätzliche Bolbu-Gegner?")
        items = sorted(
            (name for name in self._dev_seen_items if name != "FOOD"),
            key=lambda name: (-self._dev_seen_items[name], name),
        )
        if items:
            self._dev_ask("item", "Welches Item sollte überarbeitet werden?",
                          items=items)

    def _dev_feedback_resume(self):
        """Apply a once-only frozen-time correction after a complete modal queue."""
        if self._dev_feedback_opened_at is None:
            return
        elapsed = max(0.0, time.time() - self._dev_feedback_opened_at)
        self._dev_feedback_opened_at = None
        shift_round_timers(self, elapsed)
        if isinstance(self.boss, Boss):
            self.boss_fight_started_at += elapsed
            self.boss._visual_step_start += elapsed
            self.boss.teleport.next_ready_at += elapsed
        self.respawn_invincible_until += elapsed
        self.last_update_time = time.time()
        self._effect_update_time = time.monotonic()
        self._stall_clock_sample = time.monotonic()
        self.dev_recorder.event("feedback_pause_end", seconds=round(elapsed, 2))

    def _draw_dev_indicator(self):
        if self.game_state == GameState.INTRO and not self.level_editor.active:
            self._dev_button_rect = pygame.Rect(
                self.screen.get_width() - 175, 12, 160, 32,
            )
            enabled = self.dev_recorder.enabled
            surface = pygame.Surface(self._dev_button_rect.size, pygame.SRCALPHA)
            surface.fill((27, 83, 81, 215) if enabled else (25, 29, 50, 215))
            self.screen.blit(surface, self._dev_button_rect)
            pygame.draw.rect(self.screen, (136, 224, 185) if enabled
                             else (109, 138, 160), self._dev_button_rect, 1,
                             border_radius=6)
            label = "DEV+  AN  [F8]" if enabled else "DEV+  AUS  [F8]"
            text = self._dev_ui_font.render(label, True, (222, 245, 248))
            self.screen.blit(text, text.get_rect(center=self._dev_button_rect.center))
            # Visible manual checkpoint, only once the session contains data.
            if self.dev_session.active and self.dev_session.has_data:
                self._dev_save_rect = pygame.Rect(
                    self.screen.get_width() - 175, 50, 160, 31,
                )
                status = (
                    "SPEICHERFEHLER" if (self.dev_session.error or
                        self.dev_recorder.error and self.dev_recorder.active or
                        time.monotonic() < self._dev_save_notice_until
                        and not self._dev_save_success) else
                    "GESPEICHERT" if time.monotonic() < self._dev_save_notice_until
                                   and self._dev_save_success else
                    "SPEICHERN" if self.dev_session.dirty else "GESPEICHERT"
                )
                good = not self.dev_session.error and (
                    status == "GESPEICHERT"
                )
                color = (32, 88, 70) if good else (
                    (100, 35, 45) if status == "SPEICHERFEHLER"
                    else (49, 62, 91)
                )
                pygame.draw.rect(self.screen, color, self._dev_save_rect,
                                 border_radius=6)
                pygame.draw.rect(self.screen, (134, 213, 179) if good
                                 else (119, 150, 171), self._dev_save_rect,
                                 1, border_radius=6)
                caption = self._dev_ui_font.render(status, True, (231, 245, 244))
                self.screen.blit(
                    caption, caption.get_rect(center=self._dev_save_rect.center),
                )
            else:
                self._dev_save_rect = pygame.Rect(0, 0, 0, 0)
            if (self.dev_session.active and self.dev_session.rounds and
                    self.dev_session.rounds[-1].get("finished_at")):
                hint = ("F10: TEST MARKIERT" if
                        self.dev_session.rounds[-1].get("tester_intent")
                        == "intentional_test_end" else
                        "F10: TEST BEWUSST")
                label = self._dev_ui_font.render(hint, True, (179, 207, 210))
                self.screen.blit(label, label.get_rect(
                    topcenter=(self.screen.get_width() - 95, 87),
                ))
        elif (self.dev_recorder.enabled and self.game_state
              in (GameState.GAME, GameState.BOSS_FIGHT, GameState.PAUSE)):
            show_full = time.monotonic() < self._dev_badge_until
            label = "DEV+ AUFZEICHNUNG" if show_full else "DEV+"
            text = self._dev_ui_font.render(label, True, (169, 235, 223))
            rect = text.get_rect(topright=(self.screen.get_width() - 12, 10))
            backdrop = rect.inflate(12, 8)
            pygame.draw.rect(self.screen, (13, 27, 40), backdrop, border_radius=5)
            self.screen.blit(text, rect)

    def _announce_boss_phase(self, boss, stage, now):
        """Tell the player before an altered boss can start a new attack."""
        if boss.teleport.action is not None or boss.teleport.scanning():
            boss.cancel_teleport(now)
        boss.tactics.cancel(now)
        boss.defense.cancel()
        # Existing projectiles/areas finish normally; no instant attack
        # after the 1.2-second warning and the 0.65-second recovery.
        recovery_at = boss.phases.warning_ends_at + RECOVERY_SECONDS
        boss.next_proj = max(boss.next_proj, recovery_at)
        boss.next_aoe = max(boss.next_aoe, recovery_at)
        boss.tactics.next_cast_at = max(
            boss.tactics.next_cast_at, recovery_at,
        )
        self.log_combat_event(
            "boss_phase_warning", boss=boss.profile_key,
            phase=stage, title=boss.phases.stage_name(stage),
        )

    def _tick_boss_phases(self, now):
        """One progression per threshold; no repeated HP/score rewards."""
        boss = self.boss
        if not isinstance(boss, Boss) or not boss.ai_preview:
            return
        activated = boss.phases.advance(now)
        if activated is not None:
            boss.apply_phase_tuning()
            self.log_combat_event(
                "boss_phase_active", boss=boss.profile_key, phase=activated,
            )
        # If one large hit crosses two HP thresholds, both transitions get
        # a separate, visible warning instead of skipping the middle stage.
        elif boss.phases.pending_stage is None:
            pending = boss.phases.observe_health(boss.health, now)
            if pending is not None:
                self._announce_boss_phase(boss, pending, now)

    def damage_boss(self, damage, source, *, is_projectile=True):
        """Apply boss damage and process the reward/transition exactly once."""
        boss = self.boss
        if boss is None:
            return False
        if isinstance(boss, Boss) and boss.ai_preview and boss.teleport.hidden(time.time()):
            # During sinking/emerging even direct special damage cannot hit
            # an invisible or half-materialized boss.
            return False
        # A shield can only be raised by an observed incoming player shot.
        # The existing projectile-consumption path still removes that hit.
        if (is_projectile and isinstance(boss, Boss) and boss.ai_preview
                and boss.defense.consume(time.time())):
            self.log_combat_event("boss_shield_blocked", source=source)
            return False
        old_health = boss.health
        boss.health = max(0, boss.health - damage)
        self.log_combat_event("boss_damage", source=source, damage=old_health - boss.health,
                              health=boss.health)
        if is_projectile:
            self.log_combat_event("projectile_hit", projectile=source, target="boss")
        if boss.health > 0:
            # Historic standalone boss combat tests also use light-weight
            # mock objects. Only real Boss instances own phase controllers.
            if isinstance(boss, Boss) and boss.ai_preview:
                stage = boss.phases.observe_health(boss.health, time.time())
                if stage is not None:
                    self._announce_boss_phase(boss, stage, time.time())
            return False
        center = boss.get_hitbox().center
        self.boss = None
        # The defeated boss must not leave harmless but misleading purple
        # projectiles (with lingering debug hitboxes) on the arena.
        # Player and normal-enemy shots remain untouched.
        self.projectiles = [
            shot for shot in self.projectiles if not shot.get("from_boss", False)
        ]
        self.boss_flame_projectiles.clear()
        self.effect_manager.stop(getattr(boss, "aura_effect", None))
        self.boss_fight_active = False
        self.game_state = GameState.GAME
        self.boss_spawn_timer = time.time() + 60 + random.randint(0, 30)
        self.score += 100 * self.level
        self.add_achievement("Boss besiegt! Boss Down Easy Going !!")
        self.effects['boss_loot'] = time.time() + 10
        self.effect_manager.spawn("explosion", center)
        self.log_combat_event(
            "boss_defeated", source=source, score=100 * self.level,
            boss=getattr(boss, "profile_key", "classic"),
            max_health=getattr(boss, "max_health", old_health),
            duration_seconds=round(max(
                0.0, time.time() -
                getattr(self, "boss_fight_started_at", time.time()),
            ), 2),
        )
        self.round_bosses_defeated += 1
        if (self.dev_recorder.active and not self.headless
                and self._dev_boss_reviews < 3):
            self._dev_boss_reviews += 1
            self._dev_ask(
                f"boss:{getattr(boss, 'profile_key', 'classic')}:{self.round_bosses_defeated}",
                "Wie fair und spannend war dieser Bosskampf?",
            )
        return True

    def activate_portal(self, event):
        self._dev_portal_seen = self._dev_portal_seen or self.dev_recorder.active
        self.dev_recorder.event(
            "portal_activated", event_type=type(event).__name__,
            level=self.level, world=self.classic_level_name,
        )
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
        if event == "teleport":
            if self.player_count == 2:
                self.snake1[0] = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
                self.snake2[0] = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            else:
                self.snake[0] = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            self._blocked_since.clear()
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
        boss_at_start = self.boss

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
            if proj.get("from_boss", False):
                # A zero-velocity boss orb is not a meaningful attack.
                # Classic contact was already checked earlier in this frame.
                # Never keep a stationary sprite/hitbox indefinitely.
                if dx == 0 and dy == 0:
                    continue
                remaining = proj.get(
                    "lifetime_ticks", BOSS_PROJECTILE_LIFETIME_TICKS,
                ) - 1
                if remaining <= 0:
                    continue
                proj["lifetime_ticks"] = remaining
            new_x = proj['pos'][0] + dx
            new_y = proj['pos'][1] + dy
            proj['pos'] = (new_x, new_y)
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                continue
            if not proj.get("from_boss", False) and self._resolve_player_grid_projectile_hit(proj):
                continue
            new_proj.append(proj)
        # A player projectile can defeat the boss while iterating here.
        # Never reintroduce the defeated boss's bullets from the local list.
        if boss_at_start is not None and self.boss is None:
            new_proj = [
                shot for shot in new_proj if not shot.get("from_boss", False)
            ]
        self.projectiles = new_proj

    def _resolve_player_grid_projectile_hit(self, projectile):
        """Resolve collisions at the shot's new position and report consumption."""
        x, y = projectile["pos"]
        boss_hitbox = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        if self.boss and self.boss.get_rect().colliderect(boss_hitbox):
            self.damage_boss(PLAYER_PROJECTILE_DAMAGE,
                             projectile.get("projectile_type", "player_projectile"))
            return True

        # Friendly fire is not part of the Classic auto-shoot pickup.
        # New slow shots start INSIDE their owner's head tile; discarding
        # them against that head would silently erase every shot on frame 1.
        # Boss damage is resolved above; the projectile lives on otherwise.
        return False

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
            self._dev_capture_vitals("boss_grid_projectile")
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
                    self.round_enemies_defeated += 1
                    self.score += 20
                    self.add_achievement("Enemy roasted!")
                return "enemy"
        return None

    def _resolve_boss_flame_hits(self, projectile):
        if self._respawn_protection_active():
            return False
        hit = False
        for (x, y), health_attr in self._player_heads_with_health():
            head_rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if projectile.collides_with(head_rect):
                setattr(self, health_attr, getattr(self, health_attr) - projectile.damage)
                hit = True
        if hit:
            self._dev_capture_vitals("boss_flame_projectile")
        return hit

    def check_boss_collision(self, snake_head):
        if self.boss:
            boss_rect = self.boss.get_rect()
            head_x = snake_head[0] * GRID_SIZE + GRID_SIZE // 2
            head_y = snake_head[1] * GRID_SIZE + GRID_SIZE // 2
            return boss_rect.collidepoint(head_x, head_y)
        return False

    def _resolve_normal_enemy_contact(self, now):
        """Limit normal-enemy overlap damage to one hit per second per player."""
        if (not self.enemies or self.game_state == GameState.GAME_OVER
                or now < self.respawn_invincible_until):
            return False

        targets = []
        for (x, y), health_attr in self._player_heads_with_health():
            if now < self._normal_enemy_contact_ready_at.get(health_attr, 0):
                continue
            head = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if any(head.colliderect(enemy.get_hitbox()) for enemy in self.enemies):
                targets.append(health_attr)

        for health_attr in targets:
            self._normal_enemy_contact_ready_at[health_attr] = now + NORMAL_ENEMY_CONTACT_INTERVAL
            setattr(self, health_attr, getattr(self, health_attr) - NORMAL_ENEMY_CONTACT_DAMAGE)
        if targets:
            self._dev_capture_vitals("normal_enemy_contact")
        # Apply all simultaneous 2P hits before resolving the shared life.
        if targets and any(getattr(self, attr) <= 0 for attr in targets):
            self.handle_death()
        return bool(targets)

    def _boss_teleport_safety(self):
        """Authoritative landing mask: world walls, full 1P/2P bodies, items,
        enemies, active AoE and active projectiles. Tactical *aim* still uses
        only the boss's observed/remembered target, not this safety mask.
        """
        blocked = set(self._vision_blockers)
        snakes = ((self.snake,) if self.player_count == 1
                  else (self.snake1, self.snake2))
        for snake in snakes:
            blocked.update(snake)

        def mark_rect(rect):
            if rect is None or rect.width <= 0 or rect.height <= 0:
                return
            min_x = max(0, rect.left // GRID_SIZE)
            min_y = max(0, rect.top // GRID_SIZE)
            max_x = min(GRID_WIDTH, (rect.right - 1) // GRID_SIZE + 1)
            max_y = min(GRID_HEIGHT, (rect.bottom - 1) // GRID_SIZE + 1)
            blocked.update((x, y) for x in range(min_x, max_x)
                           for y in range(min_y, max_y))

        for item in self.items:
            blocked.add((item.x, item.y))
        for enemy in self.enemies:
            if hasattr(enemy, "get_hitbox"):
                mark_rect(enemy.get_hitbox())
        if self.portal is not None:
            mark_rect(self.portal.get_rect())
        for shot in self.projectiles:
            if "pos" in shot:
                x, y = shot["pos"]
                # The classic grid-shot hitbox covers an entire cell.
                blocked.add((int(x), int(y)))
        for shot in (self.flame_projectiles + self.enemy_projectiles
                     + self.boss_flame_projectiles):
            rect = (shot.get_hitbox() if hasattr(shot, "get_hitbox")
                    else getattr(shot, "rect", None))
            mark_rect(rect)

        live_zones = [
            zone for zone in self.aoe_zones if getattr(zone, "alive", False)
        ]
        if live_zones:
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    center = pygame.Vector2(
                        (x + .5) * GRID_SIZE, (y + .5) * GRID_SIZE,
                    )
                    if any(zone.is_inside(center) for zone in live_zones):
                        blocked.add((x, y))
        heads = [cell for cell, _attr in self._player_heads_with_health()]
        return blocked, heads

    def _tick_boss_teleport(self, now):
        """Telegraph -> sink -> safety-rechecked landing -> emergence.

        Triggered once in HP phases II/III by a *real boss sensor reading*.
        All sprites and their collision hitboxes use the same action state.
        A newly occupied landing cell aborts instead of telefragging players.
        """
        boss = self.boss
        if not isinstance(boss, Boss) or not boss.ai_preview:
            return False
        tele = boss.teleport
        action = tele.action
        if action is not None:
            if tele.needs_landing(now):
                # Recheck because the snakes can move during the warning.
                blocked, heads = self._boss_teleport_safety()
                if not destination_is_safe(
                    action.destination, boss.size,
                    (GRID_WIDTH, GRID_HEIGHT), blocked, heads,
                ):
                    boss.cancel_teleport(now, show_abort=True)
                    self.log_combat_event(
                        "boss_teleport_aborted", reason="landing_occupied",
                        boss=boss.profile_key, phase=action.stage,
                    )
                    return False
                boss.x, boss.y = action.destination
                boss._visual_from = boss._visual_to = (boss.x, boss.y)
                boss._visual_step_start = now
                boss.last_move = now
                tele.arrive(now)
                self.log_combat_event(
                    "boss_teleport_arrived", boss=boss.profile_key,
                    phase=action.stage, destination=action.destination,
                )
            return tele.finish(now) or tele.waiting(now)

        if (self.game_state != GameState.BOSS_FIGHT
                or boss.phases.warning_active(now)
                or now - boss.spawn_time < BOSS_SPAWN_PROTECTION):
            return False
        stage = boss.phases.stage
        reading = boss.eyes.reading
        # Phase III Wächter/Ritter explicitly receives a *magical* ability
        # to search the whole playable board, even beyond normal LOS.
        # Phase I/II and all other bosses retain normal observation rules.
        # The scan takes 1.45s and must finish before picking the current
        # 1P/2P head; it never feeds omniscience into movement or attacks.
        scanned = False
        target = None
        if tele.scanning():
            if not tele.scan_complete(now):
                return True
            heads = [cell for cell, _ in self._player_heads_with_health()]
            target = world_scan_target((boss.x, boss.y), boss.size, heads)
            tele.end_search()
            scanned = True
            self.log_combat_event(
                "boss_world_scan_complete", boss=boss.profile_key,
                target=target,
            )
            if target is None:
                tele.next_ready_at = now + 3.0
                return False
        else:
            if not tele.ready(stage, now):
                return False
            if boss.profile_key == "guardian" and stage == 3:
                if not tele.begin_search(stage, now):
                    return False
                boss.cancel_swipe(now)
                boss.defense.cancel()
                boss.tactics.cancel(now)
                quiet_until = now + WORLD_SCAN_SECONDS + 3.0
                boss.next_proj = max(boss.next_proj, quiet_until)
                boss.next_aoe = max(boss.next_aoe, quiet_until)
                boss.tactics.next_cast_at = max(
                    boss.tactics.next_cast_at, quiet_until,
                )
                self.log_combat_event(
                    "boss_world_scan_warning", boss=boss.profile_key,
                    stage=stage, scan_seconds=WORLD_SCAN_SECONDS,
                )
                return True
            if not reading.actionable or reading.predicted_cell is None:
                return False
            target = reading.predicted_cell
        blocked, heads = self._boss_teleport_safety()
        if not heads:
            tele.next_ready_at = now + 3.0
            return False
        destination = choose_destination(
            (boss.x, boss.y), boss.size, (GRID_WIDTH, GRID_HEIGHT),
            blocked, heads, target, boss.profile_key,
        )
        if destination is None:
            tele.next_ready_at = now + 3.0
            return False
        if not tele.begin((boss.x, boss.y), destination, stage, now):
            return False
        # Teleport is an *alternative* tactic, never simultaneous with Swipe,
        # Frost or an unexpected fresh attack from the former location.
        boss.cancel_swipe(now)
        boss.defense.cancel()
        boss.tactics.cancel(now)
        ready = now + 3.0
        boss.next_aoe = max(boss.next_aoe, ready)
        boss.next_proj = max(boss.next_proj, ready)
        boss.tactics.next_cast_at = max(boss.tactics.next_cast_at, ready)
        self.log_combat_event(
            "boss_teleport_warning", boss=boss.profile_key,
            style=tele.style, stage=stage,
            destination=destination, warning_seconds=1.10,
            global_scan=scanned,
        )
        return True

    def _scan_boss_defense(self, now):
        """Sense *player-owned* incoming shots only, never hidden attack data."""
        boss = self.boss
        if (not isinstance(boss, Boss) or not boss.ai_preview
                or boss.teleport.waiting(now)
                or boss.teleport.scanning()
                or boss.phases.warning_active(now)
                or now - boss.spawn_time < BOSS_SPAWN_PROTECTION):
            return
        shots = [
            IncomingShot(
                id(shot),
                (shot["pos"][0] + .5, shot["pos"][1] + .5),
                tuple(shot["dir"]),
            )
            for shot in self.projectiles
            if (not shot.get("from_boss") and "pos" in shot
                and "dir" in shot)
        ]
        for flame in self.flame_projectiles:
            if not hasattr(flame, "rect") or not hasattr(flame, "direction"):
                continue
            velocity = getattr(flame, "speed", 0) / GRID_SIZE
            shots.append(IncomingShot(
                id(flame),
                (flame.rect.centerx / GRID_SIZE, flame.rect.centery / GRID_SIZE),
                (flame.direction[0] * velocity,
                 flame.direction[1] * velocity),
                max(flame.rect.width, flame.rect.height) / (2 * GRID_SIZE),
            ))
        center = (boss.x + boss.size / 2, boss.y + boss.size / 2)
        # Keep observation counts only for the opt-in developer hitbox view.
        visible = boss.defense.visible_threats(
            center, boss.facing, boss.size, shots, self._vision_blockers,
        )
        boss._boss_shot_debug = (len(shots), len(visible))
        if boss.swipe.active(now):
            boss.swipe.last_reason = "SWIPING"
            return
        if not boss.defense.active(now) and boss.profile.swipe:
            action = boss.swipe.observe(
                (boss.x, boss.y), boss._visual_position(now), boss.size,
                visible, shots, self._vision_blockers,
                (GRID_WIDTH, GRID_HEIGHT),
                [head for head, _ in self._player_heads_with_health()],
                now,
            )
            if action is not None:
                boss.begin_swipe(action)
                boss.defense.cancel()
                self.log_combat_event(
                    "boss_swipe", target=action.destination,
                    charges=boss.swipe.charges(now),
                )
                return
        elif not boss.profile.swipe:
            boss.swipe.last_reason = "SHIELD_ONLY"
        if boss.profile.shield and boss.defense.observe(
                center, boss.facing, boss.size, shots,
                self._vision_blockers, now):
            self.log_combat_event("boss_shield_raised")

    def _tick_medusa_volley(self, now):
        """Opt-in boss attack: locked telegraph -> one impact per player.

        Existing Classic projectiles, aura, body contact and movement cadence
        remain independent. Even a relay sighting is an observed position,
        never a live player position secretly read when out of sight.
        """
        boss = self.boss
        if (not isinstance(boss, Boss) or not boss.ai_preview
                or boss.teleport.waiting(now)
                or boss.phases.warning_active(now)
                or not boss.profile.frost_throw
                or self.game_state != GameState.BOSS_FIGHT):
            return False
        tactics = boss.tactics
        if now - boss.spawn_time >= BOSS_SPAWN_PROTECTION:
            origin = (boss.x + boss.size / 2, boss.y + boss.size / 2)
            cast = tactics.cast(
                boss.eyes.reading, now, origin,
                self._vision_blockers, (GRID_WIDTH, GRID_HEIGHT),
            )
            if cast is not None:
                self.log_combat_event("medusa_frost_warning",
                                      target=cast.target)

        # Existing player protections also apply to the *new* area attack.
        if (now < self.respawn_invincible_until
                or now < self.effects["invincibility"]):
            return False
        hits = tactics.hit_players(now, self._player_heads_with_health())
        for health_attr in hits:
            setattr(self, health_attr,
                    getattr(self, health_attr) - tactics.DAMAGE)
            self.log_combat_event("medusa_frost_hit",
                                  target=health_attr, damage=tactics.DAMAGE)
        if hits:
            self._dev_capture_vitals("medusa_frost")
        # 2P damage is collected before a shared-life loss is resolved.
        if hits and any(getattr(self, key) <= 0 for key in hits):
            self.handle_death()
        return self.respawn.active or self.game_state == GameState.GAME_OVER

    def _resolve_boss_body_contact(self, now):
        if (self.boss is None or self.game_state == GameState.GAME_OVER
                or (isinstance(self.boss, Boss)
                    and (self.boss.teleport.waiting(now)
                         or self.boss.teleport.scanning()))
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
        self._dev_capture_vitals("boss_body_contact")
        self.dev_recorder.event(
            "boss_body_contact", player_health_fields=targets,
            damage_each=BOSS_BODY_DAMAGE,
            after_hp={attr: getattr(self, attr) for attr in targets},
        )
        if SOUNDS.get("damage"):
            SOUNDS["damage"].play()
        # Both players take their hit before the shared life can reset their health.
        if any(getattr(self, health_attr) <= 0 for health_attr in targets):
            self.handle_death()
        return True

    def auto_shoot_for_head(self, head, current_direction):
        slots = min(MAX_AUTO_SHOTS_PER_HEAD,
                    MAX_PLAYER_GRID_PROJECTILES - sum(
                        not shot.get("from_boss", False)
                        for shot in self.projectiles
                    ))
        if slots <= 0:
            return
        # The pickup targets the nearest real opponent, including the boss
        # for which this item is deliberately spawned. Never use a stale
        # random target after the last enemy has disappeared.
        target_cell = None
        min_dist = float("inf")
        for enemy in self.enemies:
            if time.time() - getattr(enemy, "spawn_time", 0) < 3:
                continue
            cell = (enemy.x, enemy.y)
            dist = sqrt((head[0] - cell[0]) ** 2
                        + (head[1] - cell[1]) ** 2)
            if dist < min_dist:
                min_dist, target_cell = dist, cell
        if self.boss is not None:
            boss_cell = (self.boss.x + self.boss.size / 2,
                         self.boss.y + self.boss.size / 2)
            dist = sqrt((head[0] - boss_cell[0]) ** 2
                        + (head[1] - boss_cell[1]) ** 2)
            if dist < min_dist:
                target_cell = boss_cell

        # Half the former pickup-shot speed, then cap its actual *vector*
        # magnitude to the player fireball's per-frame distance.
        shot_speed = player_grid_speed_cells_per_tick(
            self.settings["projectile_speed_factor"], GRID_SIZE,
        )
        if target_cell is not None:
            angle = atan2(target_cell[1] - head[1],
                          target_cell[0] - head[0])
        else:
            dx, dy = current_direction.value
            angle = atan2(dy, dx)
        dir_x, dir_y = cos(angle) * shot_speed, sin(angle) * shot_speed
        self.projectiles.append({
            "pos": (head[0], head[1]), "dir": (dir_x, dir_y),
            "effect": "damage", "projectile_type": "player_projectile",
        })
        self.log_combat_event("projectile_fired", projectile="player_projectile")
        # Only ONE shot per head per interval, even after repeated pickups.
        # The former stacked spread could erase a 30-HP boss in one volley.
        # A future weapon type can restore multishot with separate balancing.


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
        if self._tick_respawn():
            if isinstance(self.boss, Boss):
                self.boss.tactics.cancel(time.time())
                self.boss.defense.cancel()
                self.boss.cancel_swipe(time.time())
                self.boss.cancel_teleport(time.time())
                self.boss.phases.cancel_warning()
            return
        if not self._gameplay_active():
            if isinstance(self.boss, Boss):
                self.boss.tactics.cancel(time.time())
                self.boss.defense.cancel()
                self.boss.cancel_swipe(time.time())
                self.boss.cancel_teleport(time.time())
                self.boss.phases.cancel_warning()
            self._stall_clock_sample = None
            return
        current_time = time.time()
        if self.dev_recorder.active:
            heads = ({"1": list(self.snake[0])} if self.player_count == 1 and self.snake
                     else {str(i): list(snake[0]) for i, snake in
                           ((1, self.snake1), (2, self.snake2)) if snake})
            boss_snapshot = (
                {"type": self.boss.profile_key,
                 "cell": [self.boss.x, self.boss.y],
                 "hp": self.boss.health,
                 "phase": self.boss.phases.stage}
                if isinstance(self.boss, Boss) else None
            )
            self.dev_recorder.sample(
                level=self.level, player_heads=heads, boss=boss_snapshot,
                enemies=len(self.enemies), items=len(self.items),
                portal=self.portal_effect_type if self.portal_effect_active else None,
                world=self.classic_level_name,
            )
        effect_now = time.monotonic()
        self._advance_stall_clock(effect_now)
        self.effect_manager.update(effect_now - self._effect_update_time)
        self._effect_update_time = effect_now
        if self.frost.zones:
            self.frost.update(effect_now)
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
        # Projectile positions move exactly ONCE per gameplay update below.
        # In particular, do not advance fireballs here *and* in
        # update_projectiles() (which used to cause 2–3 steps per frame).
        invincible = current_time < self.respawn_invincible_until
        if self.effects['projectile_shoot'] > current_time:
            self.auto_shoot()

        # Normal enemy spawns are independent of the optional Auto-Shoot item.
        if (random.random() < self.settings['enemy_spawn_rate']
                and len(self.enemies) < ENEMY_LIMIT[self.player_count]):
            enemy = NormalEnemy()
            enemy.spawn_time = current_time
            self.enemies.append(enemy)
            self.dev_recorder.event(
                "enemy_spawn", kind="NormalEnemy", cell=[enemy.x, enemy.y],
                level=self.level,
            )

        # Head cells are current player positions only, including both
        # players in 2P. An opt-in admin switch can now feed these real
        # observations into a minimal movement-only behaviour pilot.
        sight_targets = (
            [(1, self.snake[0])] if self.player_count == 1 and self.snake
            else ([(1, self.snake1[0])] if self.snake1 else [])
            + ([(2, self.snake2[0])] if self.snake2 else [])
            if self.player_count == 2 else []
        )
        # Boss Medusa Eyes uses the same real 1P/2P heads and authored
        # occlusion map as NormalEnemy, but only while KI-Test is enabled.
        # Neither attacks nor boss step cadence change outside this pilot.
        if isinstance(self.boss, Boss):
            self.boss.set_ai_preview(self.enemy_ai_preview)
            self._tick_boss_phases(current_time)
            self.boss.navigation_blockers = self._vision_blockers
            if self.enemy_ai_preview:
                eye_origin = (self.boss.x + self.boss.size // 2,
                              self.boss.y + self.boss.size // 2)
                self.boss.eyes.observe(
                    eye_origin, self.boss.facing, sight_targets,
                    self._vision_blockers, current_time,
                    (GRID_WIDTH, GRID_HEIGHT),
                )
            self._tick_boss_teleport(current_time)
        self._scan_boss_defense(current_time)
        if self._tick_medusa_volley(current_time):
            return

        # Perception uses the current projectile position before its sole
        # frame move. Keep Classic hit checks *before* projectile advancement
        # to preserve the original 1P/2P once-per-flight hit order.
        for enemy in self.enemies:
            if isinstance(enemy, NormalEnemy) and hasattr(enemy, "eyes"):
                # Sample first so pursuit reacts on this movement tick.
                # Only this opt-in preview changes existing enemy movement.
                enemy.set_ai_preview(self.enemy_ai_preview)
                enemy.navigation_blockers = self._vision_blockers
                enemy.eyes.observe(
                    (enemy.x, enemy.y), enemy.facing,
                    sight_targets, self._vision_blockers, current_time,
                )
            # Pass Spielerposition für bisheriges Classic-/Bolbu-Verhalten
            if self.player_count == 1 and self.snake:
                px, py = self.snake[0]
            elif self.player_count == 2 and self.snake1:
                px, py = self.snake1[0]
            else:
                px = py = None
            if self.frost.zones and isinstance(enemy, NormalEnemy):
                factor = self.frost.movement_factor_at(enemy.x, enemy.y)
                enemy.update(px, py, movement_factor=factor)
            else:
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
            for proj in self.projectiles[:]:
                if proj.get("from_boss", False):
                    # Hostile boss bullets never damage the boss's allies.
                    continue
                proj_rect = pygame.Rect(
                    proj['pos'][0] * GRID_SIZE,
                    proj['pos'][1] * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE
                )
                if enemy_rect.colliderect(proj_rect):
                    # A player pickup shot can hit only one enemy once.
                    # Otherwise the slower bullet can deal damage on every
                    # consecutive frame while overlapping the same hitbox.
                    self.projectiles.remove(proj)
                    enemy.health -= PLAYER_PROJECTILE_ENEMY_DAMAGE
                    if enemy.health <= 0 and enemy in self.enemies:
                        self.enemies.remove(enemy)
                        self.round_enemies_defeated += 1
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
                impact_center = flame.rect.center
                self.spawn_fire_explosion(impact_center)
                self.flame_projectiles.remove(flame)
                self.frost.on_fireball_hit(impact_center, effect_now)
                if hit == "boss":
                    break


            
        # [KS_TAG: BOSS_FLAME_COLLISION]        # ----- ENEMY PROJECTILE COLLISION -----
        for proj in self.enemy_projectiles[:]:
            if self._respawn_protection_active():
                continue
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
        self._dev_capture_vitals("enemy_projectile")
        for proj in self.boss_flame_projectiles[:]:
            if self._resolve_boss_flame_hits(proj):
                self.spawn_fire_explosion(proj.rect.center)
                self.boss_flame_projectiles.remove(proj)


        # … (Spieler‑ und Boss‑Kollisionen, AoE‑Handling, Bewegung,
        #     Item‑Aufnahme, Boss‑Logik, Projektil‑Update usw. – unverändert wie besprochen) …
        # Portal interactions run before normal-enemy contact resolution.
        if self.player_count == 1 and self.snake:
            head = self.snake[0]
            head_rect = pygame.Rect(head[0] * GRID_SIZE, head[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if self.portal and head_rect.colliderect(self.portal.get_rect()):
                self.activate_portal(self.portal.event)
                self.portal_effect_active = True
                self.portal = None
        elif self.player_count == 2:
            for snake in (self.snake1, self.snake2):
                if snake:
                    head = snake[0]
                    head_rect = pygame.Rect(head[0] * GRID_SIZE, head[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if self.portal and head_rect.colliderect(self.portal.get_rect()):
                        self.activate_portal(self.portal.event)
                        self.portal_effect_active = True
                        self.portal = None
        if self._resolve_normal_enemy_contact(current_time):
            invincible = current_time < self.respawn_invincible_until
        if self.game_state == GameState.GAME_OVER:
            return
        if self.respawn.active:
            return
        if self._resolve_boss_body_contact(current_time):
            invincible = current_time < self.respawn_invincible_until
        if self.respawn.active:
            return
        if self.projectiles and current_time >= self.respawn_invincible_until and self.game_state != GameState.GAME_OVER:
            self._resolve_classic_boss_projectile_hits()
            invincible = current_time < self.respawn_invincible_until
        # Exactly one world-projectile advancement per gameplay update;
        # never repeat it inside the snake movement tick.
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
                    previous_hp = player_obj.health
                    zone.apply_effect(player_obj)
                    if self.dev_recorder.active and player_obj.health != previous_hp:
                        self.dev_recorder.event(
                            "aoe_hp_effect", player=1,
                            kind=getattr(zone, "effect_type", "unknown"),
                            hp_before=round(previous_hp, 3),
                            hp_after=round(player_obj.health, 3),
                            source_code="Dark_Snake/modules/game.py::Game.update",
                        )
                    if not hasattr(zone, "debug_triggered"):
                        print(f"DEBUG: AoE-Effekt '{zone.effect_type}' auf Singleplayer angewendet.")
                        zone.debug_triggered = True
            self.player_health = player_obj.health
            self._dev_capture_vitals("aoe_zone_aggregated")
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
                    previous_hp = p1_obj.health
                    zone.apply_effect(p1_obj)
                    if self.dev_recorder.active and p1_obj.health != previous_hp:
                        self.dev_recorder.event(
                            "aoe_hp_effect", player=1,
                            kind=getattr(zone, "effect_type", "unknown"),
                            hp_before=round(previous_hp, 3),
                            hp_after=round(p1_obj.health, 3),
                            source_code="Dark_Snake/modules/game.py::Game.update",
                        )
                    if not hasattr(zone, "debug_triggered_p1"):
                        print(f"DEBUG: AoE-Effekt '{zone.effect_type}' auf Spieler 1 angewendet.")
                        zone.debug_triggered_p1 = True
            self.player_health_p1 = p1_obj.health
            self._dev_capture_vitals("aoe_zone_aggregated")
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
                    previous_hp = p2_obj.health
                    zone.apply_effect(p2_obj)
                    if self.dev_recorder.active and p2_obj.health != previous_hp:
                        self.dev_recorder.event(
                            "aoe_hp_effect", player=2,
                            kind=getattr(zone, "effect_type", "unknown"),
                            hp_before=round(previous_hp, 3),
                            hp_after=round(p2_obj.health, 3),
                            source_code="Dark_Snake/modules/game.py::Game.update",
                        )
                    if not hasattr(zone, "debug_triggered_p2"):
                        print(f"DEBUG: AoE-Effekt '{zone.effect_type}' auf Spieler 2 angewendet.")
                        zone.debug_triggered_p2 = True
            self.player_health_p2 = p2_obj.health
            self._dev_capture_vitals("aoe_zone_aggregated")
            if self.player_health_p2 <= 0:
                self.handle_death()
        if self.respawn.active:
            return
        self.aoe_zones = [zone for zone in self.aoe_zones if zone.alive]
        if random.random() < 0.001 and len(self.aoe_zones) < 5:
            self.spawn_independent_aoe_zone()
        stall_expired = any(self._stall_active_time - started >= SNAKE_STALL_TIMEOUT
                            for started in self._blocked_since.values())
        if stall_expired:
            self.handle_self_collision()
            if self.game_state == GameState.GAME_OVER or self.respawn.active:
                return
            invincible = True
        delta = current_time - self.last_update_time
        if delta >= 1.0 / self.speed:
            self._capture_previous_snakes()
            self.last_update_time = current_time
            self_collision_protected = invincible or current_time < self.effects["invincibility"]
            if not stall_expired:
                self._advance_snakes(self_collision_protected)
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
                                    and self.settings["projectile_speed_factor"] > 0
                                    and sum(shot.get("from_boss", False) for shot in self.projectiles)
                                    < MAX_BOSS_GRID_PROJECTILES):
                                # Aim from the *boss centre*, not the top-left
                                # cell. A player at the old origin could generate
                                # (0, 0), leaving a permanent purple ball.
                                aim_x, aim_y = self._boss_projectile_heading(target)
                                dx = 1 if aim_x > 0 else -1 if aim_x < 0 else 0
                                dy = 1 if aim_y > 0 else -1 if aim_y < 0 else 0
                                boss_proj_img = random.choice(BOSS_PROJECTILES) if BOSS_PROJECTILES else PROJECTILE_IMG
                                proj = {'pos': (self.boss.x, self.boss.y),
                                        'dir': (dx * self.settings['projectile_speed_factor'], dy * self.settings['projectile_speed_factor']),
                                        "effect": "damage",
                                        "from_boss": True,
                                        "projectile_type": "boss_projectile",
                                        "lifetime_ticks": BOSS_PROJECTILE_LIFETIME_TICKS,
                                        "image": boss_proj_img,
                                        "scale": self.boss.size}
                                self.projectiles.append(proj)
                                self.log_combat_event("projectile_fired", projectile="boss_projectile")
            if random.random() < 0.005 * self.settings['difficulty'] and len(self.items) < 5:
                self.spawn_new_item()

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
    def handle_item_pickup(self, item, *, source="field"):
        current_time = time.time()
        before_item = self._dev_item_state(current_time) if self.dev_recorder.active else None
        if self.dev_recorder.active and source == "field":
            name = item.type.name
            self._dev_seen_items[name] = self._dev_seen_items.get(name, 0) + 1
        self.dev_recorder.event(
            "item_pickup", item=item.type.name, source=source,
            cell=[item.x, item.y], level=self.level,
        )
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
            self.handle_item_pickup(Item(random.choice(rewards)), source="loot_box")
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
            self._dev_bolbu_seen = self._dev_bolbu_seen or (spawn_count > 0 and self.dev_recorder.active)
            self.dev_recorder.event("enemy_spawn", kind="BolbuEnemy", count=spawn_count, source="item")

        elif item.type == ItemType.PROJECTILE_SHOOT:
            self.effects['projectile_shoot'] = max(self.effects['projectile_shoot'], current_time) + 900
            # Repeated pickups extend the existing effect, not the damage
            # output or number of projectiles fired per salvo.
            self.extra_auto_shots = 0
            # Make the newly collected pickup fire on the next playable
            # update instead of looking inert for up to two seconds.
            interval = max(0, self.settings.get('auto_shoot_interval', 0.5))
            self.last_auto_shoot = current_time - interval
            self.last_auto_shoot1 = current_time - interval
            self.last_auto_shoot2 = current_time - interval
            self.score += 40
            self.experience += 20
            self.add_achievement("Auto-Shoot aktiviert!")
        if before_item is not None:
            self.dev_recorder.event(
                "item_applied", item=item.type.name, source=source,
                before=before_item, after=self._dev_item_state(current_time),
                source_code="Dark_Snake/modules/game.py::Game.handle_item_pickup",
            )
        if self.experience >= self.exp_to_next_level:
            self.level_up()

    def _safe_classic_respawn_cells(self):
        """Use the standard start cells if clear; otherwise find nearby safe ones."""
        def clear(cell):
            x, y = cell
            box = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if any(box.colliderect(enemy.get_hitbox()) for enemy in self.enemies):
                return False
            if self.boss and box.colliderect(self.boss.get_rect()):
                return False
            if self.portal and box.colliderect(self.portal.get_rect()):
                return False
            if any(box.colliderect(shot.get_hitbox() if hasattr(shot, "get_hitbox") else shot.rect)
                   for shot in self.enemy_projectiles + self.boss_flame_projectiles):
                return False
            if any(box.colliderect(pygame.Rect(shot["pos"][0] * GRID_SIZE,
                                              shot["pos"][1] * GRID_SIZE,
                                              GRID_SIZE, GRID_SIZE))
                   for shot in self.projectiles):
                return False
            center = pygame.Vector2(box.center)
            if any(zone.alive and zone.effect_type == "damage" and zone.is_inside(center)
                   for zone in self.aoe_zones):
                return False
            return True

        return safe_spawn_cells(self.player_count, GRID_WIDTH, GRID_HEIGHT, clear)

    def _begin_respawn(self):
        """Restart both Classic heads and hold the entire game for three seconds."""
        locations = self._safe_classic_respawn_cells()
        if self.player_count == 2:
            self.snake1, self.snake2 = [locations[0]], [locations[1]]
            self.snake_direction1 = self.next_direction1 = Direction.RIGHT
            self.snake_direction2 = self.next_direction2 = Direction.RIGHT
            self.player_health_p1 = self.player_health_p2 = 100
        else:
            self.snake = [locations[0]]
            self.snake_direction = self.next_direction = Direction.RIGHT
            self.player_health = 100
        self._dev_capture_vitals("respawn")
        self._reset_snake_stalls()
        self._reset_snake_interpolation()
        now = time.time()
        self.respawn.begin(now)
        if isinstance(self.boss, Boss):
            self.boss.tactics.cancel(now)
            self.boss.defense.cancel()
            self.boss.cancel_swipe(now)
            self.boss.cancel_teleport(now)
            self.boss.phases.cancel_warning()
        self._respawn_recent = True
        self.respawn_invincible_until = now + RESPAWN_SECONDS + POST_RESPAWN_PROTECTION
        self._effect_update_time = time.monotonic()
        if not self.headless and SOUNDS.get("dice"):
            SOUNDS["dice"].play()

    def _respawn_protection_active(self):
        """Protect only the new countdown respawn from all hostile shots."""
        return self._respawn_recent and time.time() < self.respawn_invincible_until

    def _tick_respawn(self):
        """Advance the overlay clock without updating enemies or moving either head."""
        if not self.respawn.active:
            return False
        now = time.time()
        playing = (self.game_state in (GameState.GAME, GameState.BOSS_FIGHT)
                   and not self.admin_panel.active and not self.level_editor.active)
        if self.respawn.step(now, playing=playing):
            # Include time in PAUSE/editor: the world was frozen for that, too.
            frozen_wall_seconds = max(0.0, now - self.respawn.began_at)
            shift_round_timers(self, frozen_wall_seconds)
            self.last_update_time = now
            self._effect_update_time = time.monotonic()
            self.respawn_invincible_until = now + POST_RESPAWN_PROTECTION
            self._stall_clock_sample = time.monotonic()
            self._reset_snake_interpolation()
            if not self.headless and SOUNDS.get("powerup"):
                SOUNDS["powerup"].play()
        # Even on the GO frame no movement or new projectiles are produced.
        return True

    def _begin_death_soul(self, players, *, final):
        """Capture the dead head(s) before respawn changes their positions."""
        snakes = {1: self.snake} if self.player_count == 1 else {
            1: self.snake1, 2: self.snake2,
        }
        centers = tuple(
            ((snakes[player][0][0] + 0.5) * GRID_SIZE,
             (snakes[player][0][1] + 0.5) * GRID_SIZE)
            for player in players if player in snakes and snakes[player]
        )
        self.round_death_count += 1
        self._death_soul_event = DeathSoulEvent(
            centers=centers,
            tier=3 if final else min(3, self.round_death_count),
            began_at=time.time(),
            final=final,
        )
        self._death_soul_frozen_world = None

    def _draw_death_soul(self, elapsed):
        if self._death_soul_event is None:
            return
        if self._death_soul_visual is None:
            self._death_soul_visual = DeathSoulVisual()
        self._death_soul_visual.draw(self.screen, self._death_soul_event, elapsed)

    def _sync_career_progress(self):
        """Recover saved-but-not-awarded rounds on startup or at Game Over."""
        try:
            self.career_snapshot = self._career_ledger.sync(self._round_journal)
            self.career_progress_error = None
            return True
        except (OSError, ValueError, TypeError) as exc:
            self.career_progress_error = str(exc)
            record_event(f"Karriererang-Fortschritt konnte nicht gespeichert werden: {exc}")
            return False

    def _sync_skin_inventory(self):
        """Reconcile verified cosmetics off the frame loop, then update the UI."""
        try:
            registry = skin_registry()
            if self.career_snapshot is None:
                raise ValueError("Career data unavailable for cosmetics.")
            snapshot = self._skin_inventory.sync(
                self.career_snapshot, registry, existing_settings=self.settings,
            )
            self.skin_inventory_snapshot = snapshot
            self.skin_inventory_error = None
            self.options_menu.apply_skin_inventory(registry, snapshot)
            return True
        except (OSError, ValueError, TypeError) as exc:
            self.skin_inventory_error = str(exc)
            record_event(f"Snake-Inventar konnte nicht synchronisiert werden: {exc}")
            # Fail closed with free starter skins; keep corrupt save file intact.
            try:
                registry = skin_registry()
                from modules.skin_inventory import starter_inventory
                fallback = starter_inventory(registry)
                self.skin_inventory_snapshot = fallback
                self.options_menu.apply_skin_inventory(registry, fallback)
            except (OSError, ValueError) as fallback_exc:
                record_event(f"Snake-Inventar-Katalog nicht nutzbar: {fallback_exc}")
            return False

    def _finalize_round_progress(self, reason):
        """Snapshot only authoritative counters, once, after final Game Over."""
        token = self._round_token
        if (not self._record_completed_rounds or token is None
                or self._round_recorded or self.game_state != GameState.GAME_OVER):
            return False
        was_recording = self.dev_recorder.active
        self._dev_capture_vitals("round_end", checkpoint=True)
        self.dev_recorder.event(
            "round_summary", reason=reason, score=self.score, level=self.level,
            enemies_defeated=self.round_enemies_defeated,
            bosses_defeated=self.round_bosses_defeated,
            items_collected=self.round_items_collected,
            lives_lost=self.round_death_count,
        )
        report_ok = self.dev_recorder.finish(reason)
        self._dev_last_round_id = token["round_id"]
        boss_names = [
            event.get("data", {}).get("boss")
            for event in self.dev_recorder.events
            if event.get("type") == "boss_spawn"
        ]
        final_hp = (
            {"1": round(self.player_health, 2)}
            if self.player_count == 1 else
            {"1": round(self.player_health_p1, 2),
             "2": round(self.player_health_p2, 2)}
        )
        self.dev_session.round_end(
            token, reason, report_saved=report_ok, summary={
                "score": self.score,
                "level": self.level,
                "enemies_defeated": self.round_enemies_defeated,
                "bosses_defeated": self.round_bosses_defeated,
                "items_collected": self.round_items_collected,
                "lives_lost": self.round_death_count,
                "lives_remaining": self.lives,
                "end_hp": final_hp,
                "bosses_seen": boss_names[-8:],
            },
        )
        self._dev_end_pending = was_recording and not self.headless
        try:
            snapshot = completed_round(
                token, reason=reason, score=self.score, level=self.level,
                enemies=self.round_enemies_defeated,
                bosses=self.round_bosses_defeated,
                items=self.round_items_collected,
                lives_lost=self.round_death_count,
            )
            # Saved round history stays authoritative; a failed career save is
            # reconciled by UUID at the next real startup or Game Over.
            self._round_journal.append(snapshot)
            self._round_recorded = True
            self.round_progress_error = None
            self.round_career_xp = xp_for_round(snapshot)
            if self._sync_career_progress():
                inventory_ok = self._sync_skin_inventory()
                try:
                    self.round_career_result = career_ceremony_for_round(
                        snapshot["round_id"], self.career_snapshot,
                        self.skin_inventory_snapshot if inventory_ok else None,
                        skin_registry() if inventory_ok else None,
                    )
                except (OSError, ValueError, TypeError) as exc:
                    # Keep committed career and inventory data intact. A
                    # missing/broken presentation must never block Game Over.
                    record_event(f"Karriere-Abschluss konnte nicht angezeigt werden: {exc}")
            return True
        except (OSError, ValueError, TypeError) as exc:
            self.round_progress_error = str(exc)
            if self.dev_session.active:
                self.dev_session.event("session_warning", code="round_progress_save_failed")
                self.dev_session.checkpoint("round_progress_failure")
            record_event(f"Rundenfortschritt konnte nicht gespeichert werden: {exc}")
            return False

    def handle_self_collision(self):
        if self.respawn.active:
            return
        stalled_players = tuple(sorted(self._blocked_since)) or (1,)
        self._blocked_since.clear()
        # Spiele den Schadens-Sound (sofern vorhanden)
        if SOUNDS.get("damage"):
            SOUNDS["damage"].play()
        # Ziehe ein Leben ab, aber nur, wenn noch Leben übrig sind
        self.lives -= 1
        self._dev_capture_vitals("self_stall_life_lost", checkpoint=True)
        print("DEBUG: Stillstand – Leben abgezogen, verbleibende Leben:", self.lives)
        self._begin_death_soul(stalled_players, final=self.lives <= 0)

        if self.lives > 0:
            self._begin_respawn()
        else:
            # Falls keine Leben mehr vorhanden sind, gehe auf Game Over
            self.metrics.cancel_pending()
            self.game_state = GameState.GAME_OVER
            self.game_over_time = time.time()
            self._finalize_round_progress("self_stall")
        if len(self.leaderboard) < 10 or self.score > self.leaderboard[-1][1]:
            self.leaderboard_mode = True

    def handle_death(self):
        if self.respawn.active or self.game_state == GameState.GAME_OVER:
            return
        if self.player_count == 1:
            if self.player_health > 0:
                return
        elif self.player_count == 2:
            if self.player_health_p1 > 0 and self.player_health_p2 > 0:
                return
        self._blocked_since.clear()
        if SOUNDS.get("gameover"):
            SOUNDS["gameover"].play()
        snake = self.snake if self.player_count == 1 else self.snake1
        if snake:
            self.effect_manager.spawn(
                "death", ((snake[0][0] + 0.5) * GRID_SIZE,
                          (snake[0][1] + 0.5) * GRID_SIZE), {"lifetime": 1.0})
        self.lives -= 1
        self._dev_capture_vitals("life_lost", checkpoint=True)
        if self.player_count == 1:
            affected = (1,)
        else:
            affected = tuple(
                player for player, hp in ((1, self.player_health_p1),
                                          (2, self.player_health_p2)) if hp <= 0
            ) or (1,)
        self._begin_death_soul(affected, final=self.lives <= 0)
        if self.lives <= 0:
            self.metrics.cancel_pending()
            self.game_state = GameState.GAME_OVER
            self.game_over_time = time.time()
            self._finalize_round_progress("life_depleted")
            if len(self.leaderboard) < 10 or self.score > self.leaderboard[-1][1]:
                self.leaderboard_mode = True
        else:
            self._begin_respawn()

    def _handle_level_editor_event(self, event, actions=()):
        editor = self.level_editor
        key = event.key if event.type == pygame.KEYDOWN else None
        if editor.active:
            if event.type == pygame.QUIT:
                editor.request_close(sys.exit)
            elif event.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED):
                self._resize_editor_window()
            elif key == pygame.K_F2:
                if editor.playtest is not None:
                    editor.stop_playtest()
                else:
                    editor.toggle()
            elif (key == pygame.K_TAB and not editor.dialog_open and editor.playtest is None
                  and not editor.library_search_focused):
                if not self._menu_suspended:
                    editor.request_close(self._toggle_admin_panel)
            else:
                editor.handle_event(event, actions)
            return True
        if key == pygame.K_F2 and self.game_state != GameState.CONTROLS:
            self._open_level_editor()
            return True
        return False

    def handle_events(self):
        events = pygame.event.get()
        read_ns = self.metrics.stamp()
        for event in events:
            if event.type == pygame.QUIT:
                if not self._handle_level_editor_event(event):
                    self._dev_quit()
                continue
            # A feedback modal owns all input. No controls leak into gameplay.
            if self.dev_feedback.active:
                subject = self.dev_feedback.current[0]
                before = len(self.dev_recorder.report.get("feedback", [])) if self.dev_recorder.report else 0
                dismissed = self.dev_feedback.handle_event(
                    event, self.dev_recorder, self.screen.get_size(),
                )
                if dismissed and self.dev_session.active:
                    feedback = self.dev_recorder.report.get("feedback", []) if self.dev_recorder.report else []
                    saved = len(feedback) > before
                    answer = feedback[-1] if saved else {}
                    self.dev_session.feedback(
                        subject, rating=answer.get("rating"), saved=saved,
                        item_verdict=answer.get("item_verdict"),
                    )
                if not self.dev_feedback.active:
                    self._dev_feedback_resume()
                continue
            if (self.dev_session.active and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_F9 and
                    self.game_state != GameState.CONTROLS):
                self._dev_mark_issue()
                continue
            if (self.dev_session.active and event.type == pygame.KEYDOWN
                    and event.key == pygame.K_F10 and
                    self.game_state in (GameState.INTRO, GameState.GAME_OVER)
                    and not self.level_editor.active):
                self._dev_mark_test_intent()
                continue
            if self.game_state == GameState.INTRO and not self.level_editor.active:
                if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                        and self._dev_save_rect.collidepoint(event.pos)):
                    self._dev_save_session()
                    continue
                if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                        and self._dev_button_rect.collidepoint(event.pos)):
                    self._toggle_dev_recorder()
                    continue
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F8:
                    self._toggle_dev_recorder()
                    continue
            # Do not accept leaderboard names or menu clicks behind the final
            # 2.4-second death animation. Window close remains available.
            if (self.game_state == GameState.GAME_OVER and
                    self._death_soul_event is not None and
                    self._death_soul_event.final and
                    0 <= time.time() - self._death_soul_event.began_at
                    < FINAL_DEATH_SECONDS):
                continue
            if self.game_state == GameState.CONTROLS:
                self.controls_menu.handle_event(event)
                continue
            playtest = self.level_editor.playtest
            player_count = self.player_count if playtest is None else playtest.player_count
            if self.game_state == GameState.INTRO and not self.level_editor.active:
                player_count = None
            actions = self.input.actions_for(event, player_count=player_count)
            if self._handle_level_editor_event(event, actions):
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self._toggle_admin_panel()
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.admin_panel.active:
                    self.admin_panel.close()
                    continue
            # An open developer tool owns all input; gameplay never sees it.
            if self.admin_panel.active:
                self.admin_panel.handle_event(event)
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.game_state not in (GameState.GAME, GameState.BOSS_FIGHT,
                                           GameState.PAUSE, GameState.SIMULATION):
                    self.set_state(self.intro_state())
                    continue
            if self.game_state == GameState.SETTINGS:
                self.options_menu.handle_event(event)
            elif self.game_state == GameState.SIMULATION:
                self.simulation_menu.handle_event(event)
            elif self.game_state == GameState.CUSTOMIZATION:
                self.custom_menu.handle_event(event)
            elif self.game_state == GameState.INTRO:
                self.main_menu.layout(self.screen.get_size())
                self.main_menu.handle_event(event, actions)
            elif self.game_state == GameState.LEADERBOARD:
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                    self.leaderboard_back_button.check_hover(event.pos)
                    self.leaderboard_back_button.handle_event(event)
            elif self.game_state == GameState.PAUSE:
                if "pause" in actions or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self._resume_game()
                    continue
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                    for btn in self.pause_buttons:
                        btn.check_hover(event.pos)
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

        if self.respawn.active:
            # Buffer one direction per player, including a left turn from the
            # initial RIGHT heading: the newly spawned snake has length one.
            for player in range(1, self.player_count + 1):
                suffix = "" if self.player_count == 1 else str(player)
                for name, direction in DIRECTION_ACTIONS.items():
                    if f"p{player}_{name}" in actions:
                        setattr(self, f"next_direction{suffix}", direction)
            return  # No shooting or special effect during countdown.

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
        self._draw_dev_indicator()
        if self.dev_feedback.active:
            self.dev_feedback.draw(self.screen, SNAKE_HEAD_IMG)
        if (self.metrics.enabled and not self.admin_panel.active and not self.level_editor.active
                and self.game_state in (GameState.GAME, GameState.BOSS_FIGHT)):
            self.metrics.draw(self.screen)
        before_present = self.metrics.stamp()
        pygame.display.update()
        self.dev_recorder.frame_mark(
            game_active=(not self.dev_feedback.active and self.game_state
                         in (GameState.GAME, GameState.BOSS_FIGHT)),
        )
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
            death = self._death_soul_event
            if (death is not None and death.final and
                    0 <= time.time() - death.began_at < FINAL_DEATH_SECONDS):
                # Freeze the world throughout the entire three-layer transition.
                if self._death_soul_frozen_world is None:
                    self.draw_game(include_hud=False)
                    self._death_soul_frozen_world = self.screen.copy()
                self.screen.blit(self._death_soul_frozen_world, (0, 0))
                if self._death_fog_visual is None:
                    self._death_fog_visual = AbyssFogVisual()
                self._death_fog_visual.draw(
                    self.screen, time.time() - death.began_at
                )
            else:
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
        if self.game_state in (GameState.GAME, GameState.BOSS_FIGHT, GameState.PAUSE):
            self.draw_hud()
            self.achievement_manager.draw_achievements(self.screen)
            self.achievement_manager.draw_portal_event(self.screen)
        if (self.respawn.active and
                self.game_state in (GameState.GAME, GameState.BOSS_FIGHT)):
            if self._respawn_visual is None:
                self._respawn_visual = FrostRespawnVisual()
            heads = self._player_heads_with_health()
            head_centers = [(pos[0] * GRID_SIZE + GRID_SIZE // 2,
                             pos[1] * GRID_SIZE + GRID_SIZE // 2)
                            for pos, _ in heads]
            self._respawn_visual.draw(self.screen, self.respawn, head_centers)
        death = self._death_soul_event
        if death is not None:
            if (death.final and self.game_state == GameState.GAME_OVER):
                self._draw_death_soul(time.time() - death.began_at)
            elif (not death.final and self.respawn.active and
                  self.game_state in (GameState.GAME, GameState.BOSS_FIGHT)):
                self._draw_death_soul(self.respawn.elapsed)
        self.admin_panel.draw(self.screen)

    def _draw_head_badge(self, player, x, y):
        """Reuse the same chosen head as gameplay; no separate life-skin setting."""
        chosen = self.options_menu.get_skin_image(
            "Heads", self.settings.get(f"custom_head_p{player}")
        )
        source = chosen if chosen is not None else (
            SNAKE_HEAD_IMG if player == 1 else SNAKE_HEAD_BETA
        )
        # scale_sprite already caches resized read-only surfaces.
        icon = scale_sprite(source, (26, 26))
        border = pygame.Rect(x - 2, y - 2, 30, 30)
        pygame.draw.rect(self.screen, (22, 13, 36), border, border_radius=5)
        pygame.draw.rect(self.screen, (153, 123, 186), border, 2, border_radius=5)
        self.screen.blit(icon, (x, y))

    def draw_hud(self):
        score_txt = pygame.font.SysFont('Arial', 30).render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_txt, (20, 10))
        level_txt = pygame.font.SysFont('Arial', 20).render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_txt, (20, 45))
        if self.player_count == 1:
            # Every remaining life shows the head the player actually selected.
            for i in range(max(0, self.lives)):
                self._draw_head_badge(1, WINDOW_WIDTH - 39 - 34 * i, 12)
            self.draw_health_bar()
        elif self.player_count == 2:
            # Classic uses ONE shared life pool, but independent player health.
            team_label = self._hud_badge_font.render(
                f"TEAM-LEBEN: {max(0, self.lives)}", True, WHITE
            )
            self.screen.blit(
                team_label, (WINDOW_WIDTH // 2 - team_label.get_width() // 2, 17)
            )
            draw_health_bar_two(self)
            self._draw_head_badge(1, 232, 80)
            self._draw_head_badge(2, WINDOW_WIDTH - 258, 80)
            self.screen.blit(self._hud_badge_font.render("P1", True, WHITE), (234, 111))
            self.screen.blit(
                self._hud_badge_font.render("P2", True, WHITE),
                (WINDOW_WIDTH - 256, 111),
            )

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
        self.main_menu.draw(self.screen)

    def _draw_boss_medusa_debug(self, boss):
        """Developer-only: visible/sensed target and persistent remote eyes."""
        if not self.enemy_ai_preview or not boss.ai_preview:
            return
        origin = (boss.x + boss.size // 2, boss.y + boss.size // 2)
        center = (round((origin[0] + .5) * GRID_SIZE),
                  round((origin[1] + .5) * GRID_SIZE))
        reading = boss.eyes.reading
        color = ((220, 135, 235) if reading.kind == "VISIBLE"
                 else (115, 206, 255) if reading.kind == "RELAY"
                 else (166, 154, 188))
        pygame.draw.circle(
            self.screen, color, center,
            round(boss.eyes.profile.radius_cells * GRID_SIZE), 1,
        )
        if reading.last_known_cell is not None:
            target = (round((reading.last_known_cell[0] + .5) * GRID_SIZE),
                      round((reading.last_known_cell[1] + .5) * GRID_SIZE))
            pygame.draw.line(self.screen, color, center, target, 1)
        if reading.predicted_cell is not None and reading.kind == "VISIBLE":
            p = reading.predicted_cell
            pygame.draw.circle(self.screen, (230, 190, 135),
                               (round((p[0] + .5) * GRID_SIZE),
                                round((p[1] + .5) * GRID_SIZE)), 4, 1)
        for eye in boss.eyes.remote:
            eye_pos = (round((eye.cell[0] + .5) * GRID_SIZE),
                       round((eye.cell[1] + .5) * GRID_SIZE))
            pygame.draw.circle(self.screen, (115, 206, 255), eye_pos,
                               round(4 * GRID_SIZE), 1)
            pygame.draw.circle(self.screen, (215, 225, 255), eye_pos, 5, 2)
        # Small, explicit diagnosis: shots present vs. actually visible and
        # approaching. No extra permanent HUD, only KI-Test + Hitbox debug.
        shots, threats = boss._boss_shot_debug
        reason = boss.swipe.last_reason
        if boss.defense.active(time.time()):
            reason = "SHIELD"
        label = (f"{boss.profile.name} P{boss.phases.stage}"
                 f"{'→' + str(boss.phases.pending_stage) if boss.phases.pending_stage else ''}"
                 f"  PROJ {shots}/{threats}  SWIPE "
                 f"{boss.swipe.charges(time.time())}/2  {reason}")
        image = self._enemy_ai_debug_font.render(
            label, True, (217, 226, 254),
        )
        text_x = max(0, min(
            WINDOW_WIDTH - image.get_width() - 6,
            boss.x * GRID_SIZE,
        ))
        text_y = max(36, boss.y * GRID_SIZE - 34)
        backing = pygame.Rect(
            text_x - 3, text_y - 2,
            image.get_width() + 6, image.get_height() + 4,
        )
        pygame.draw.rect(self.screen, (16, 22, 31), backing, border_radius=3)
        self.screen.blit(image, (text_x, text_y))

    def _draw_enemy_sight_debug(self, enemy):
        """Visualise sensed targets without affecting runtime AI or hitboxes."""
        sensor = enemy.eyes
        x, y = (enemy.x * GRID_SIZE + GRID_SIZE // 2,
                enemy.y * GRID_SIZE + GRID_SIZE // 2)
        reach = round(sensor.profile.radius_cells * GRID_SIZE)
        tint = (115, 239, 178) if sensor.result.visible else (115, 160, 202)
        pygame.draw.circle(self.screen, tint, (x, y), reach, 1)
        if (self.enemy_ai_preview
                and sensor.profile.alert_radius_cells is not None
                and sensor.result.kind in ("VISIBLE", "SEARCHING")):
            # Faint outer halo = extended range *after* detection.
            # Only the developer Hitbox view draws this extra geometry.
            pygame.draw.circle(
                self.screen, (125, 94, 183), (x, y),
                round(sensor.profile.alert_radius_cells * GRID_SIZE), 1,
            )
        if sensor.profile.fov_degrees < 360:
            angle = atan2(enemy.facing[1], enemy.facing[0])
            half = sensor.profile.fov_degrees * pi / 360
            for direction in (angle - half, angle + half):
                point = (round(x + reach * cos(direction)),
                         round(y + reach * sin(direction)))
                pygame.draw.line(self.screen, tint, (x, y), point, 1)
        if sensor.result.last_known_cell is not None:
            cell = sensor.result.last_known_cell
            target = (cell[0] * GRID_SIZE + GRID_SIZE // 2,
                      cell[1] * GRID_SIZE + GRID_SIZE // 2)
            line_color = ((90, 248, 143) if sensor.result.visible
                          else (218, 186, 103))
            pygame.draw.line(self.screen, line_color, (x, y), target, 2)
            pygame.draw.circle(self.screen, line_color, target, 5, 1)
        if self.enemy_ai_preview:
            # Developer-only, small state marker: P patrol, C chase,
            # S search, G guard, R retreat. No HUD in normal play.
            state = getattr(enemy, "behavior_state", "PATROL")
            letter = state[:1]
            label = self._enemy_ai_debug_font.render(letter, True, tint)
            self.screen.blit(label, (x + 9, y - 20))

    def draw_game(self, *, include_hud=True):
        # 1. Raster (Hintergrund) zeichnen – unterste Ebene
        self.screen.blit(self.background, (0, 0))
        self.effect_manager.draw(self.screen, "background")
        # 2. AoE-Effekte zeichnen – liegen zwischen Raster und dynamischen Objekten
        self.frost.draw(self.screen)
        if isinstance(self.boss, Boss) and self.boss.ai_preview:
            draw_medusa_volley(
                self.screen, self.boss.tactics.volley,
                time.time(), GRID_SIZE,
            )
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
        head_centers = []
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
                    head_centers.append((round(x + GRID_SIZE / 2), round(y + GRID_SIZE / 2)))
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
                    head_centers.append((round(x + GRID_SIZE / 2), round(y + GRID_SIZE / 2)))
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
                    head_centers.append((round(x + GRID_SIZE / 2), round(y + GRID_SIZE / 2)))
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

        if self._roof_objects:
            board = pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
            draw_roof_objects(self.screen, board, self._roof_objects, self._roof_visibility,
                              head_centers=head_centers)

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
                if isinstance(e, NormalEnemy) and hasattr(e, "eyes"):
                    # Existing hitbox developer toggle doubles as an eyes
                    # debugger: radius, facing wedge, detected/last-seen head.
                    self._draw_enemy_sight_debug(e)
            if isinstance(self.boss, Boss):
                self._draw_boss_medusa_debug(self.boss)
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
        """D20 banner on top; matching FrostAge result panel directly underneath."""
        if self._dice_banner is None:
            artwork = load_image("Random_D20-removebg-preview.png", "hud")
            self._dice_banner = pygame.transform.smoothscale(artwork, (330, 51))
        banner_rect = self._dice_banner.get_rect(
            midbottom=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60)
        )
        self.screen.blit(self._dice_banner, banner_rect)
        if self._dice_visual is None:
            self._dice_visual = FrostDiceResultVisual()
        self._dice_visual.draw(
            self.screen, self.dice_result, display_until=self.dice_display_until
        )


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
        """Abyss farewell, preserving leaderboard input and existing button actions."""
        if self._dev_end_pending:
            self._dev_end_pending = False
            self._dev_ask_round_end()
        if self._game_over_visual is None:
            self._game_over_visual = DarkAbyssGameOver()
        # The reward stone occupies the right half of large windows. Move the
        # two real clickable buttons (not just their painted labels) into the
        # left summary column. Restore their usual positions when no stone
        # is shown; no changes to Button callbacks or keyboard navigation.
        from modules.game_over_visual import tombstone_scene_layout
        award_or_warning = (self.round_career_result is not None
                            or (self._round_token is not None
                                and self._record_completed_rounds))
        scene = (tombstone_scene_layout(self.screen.get_size())
                 if award_or_warning else None)
        if scene is None:
            button_positions = (WINDOW_WIDTH // 2 - 228,
                                WINDOW_WIDTH // 2 + 16)
        else:
            left, panel_width, _ = scene
            first_x = left + (panel_width - 2 * 212 - 24) // 2
            button_positions = (first_x, first_x + 236)
        for button, x in zip(self.game_over_buttons, button_positions):
            button.rect.topleft = (x, 520)
        self._game_over_visual.draw(
            self.screen,
            score=self.score,
            level=self.level,
            enemies=self.round_enemies_defeated,
            items=self.round_items_collected,
            bosses=self.round_bosses_defeated,
            players=self.player_count,
            highscore_entry=self.leaderboard_mode,
            name_input=self.name_input,
            buttons=self.game_over_buttons,
            career=self.round_career_result,
            career_warning=bool(
                self._round_token is not None
                and self._record_completed_rounds
                and self.round_career_result is None
            ),
            # New round, new ceremony timer; the death fog does not consume
            # the reward's visible time (starts when Dark Abyss is first drawn).
            reward_sequence=self.game_over_time,
        )


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
        self.leaderboard_back_button.draw(self.screen)

    def run_frame(self):
        start = self.metrics.stamp()
        was_playing = self._gameplay_active()
        # A frame that starts behind an overlay may resume gameplay via input.
        if not was_playing:
            self._stall_clock_sample = None
        feedback_was_active = self.dev_feedback.active
        self.handle_events()
        after_events = self.metrics.stamp()
        if feedback_was_active or self.dev_feedback.active:
            # Freeze ALL gameplay and countdown updates while writing feedback.
            # On dismissal, shift live timers by the frozen duration.
            self.metrics.record_phase("events", start, after_events)
            self.draw()
            return
        in_countdown = self._tick_respawn()
        if not in_countdown and self._gameplay_active():
            self.update()
            self._dev_capture_vitals("unattributed")
        elif was_playing:
            self._suspend_stall_clock()
        if self.level_editor.playtest is not None:
            self.level_editor.playtest.update(time.monotonic())
        after_update = self.metrics.stamp()
        self.metrics.record_phase("events", start, after_events)
        self.metrics.record_phase("update", after_events, after_update)
        self.draw()
        self.dev_session.maybe_autosave()

    def run(self):
        try:
            while True:
                self.run_frame()
                self.clock.tick(FPS)
        finally:
            # Also covers editor-specific SystemExit paths.
            self._dev_shutdown()

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
        """Build the current round's background over the standard backdrop."""
        from modules.graphics import get_tile

        surf = self.default_background_surface.copy()
        for y, row in enumerate(getattr(self, "level_map", None) or ()):
            for x, tile in enumerate(row):
                if tile:
                    img = get_tile(tile)
                    if img:
                        surf.blit(img, (x * GRID_SIZE, y * GRID_SIZE))
        self.level_background_surface = surf
        return surf
    def _boss_projectile_heading(self, target):
        """Direction from the *centre* of the boss to the target's head.

        When both occupy the same centre tile, retain the last nonzero
        facing or fall back to EAST; never spawn a zero-speed magic orb.
        """
        if self.boss is None:
            return (1.0, 0.0)
        dx = target[0] + 0.5 - (self.boss.x + self.boss.size / 2)
        dy = target[1] + 0.5 - (self.boss.y + self.boss.size / 2)
        if abs(dx) + abs(dy) < 1e-9:
            facing = getattr(self.boss, "facing", (1, 0))
            dx, dy = facing if facing != (0, 0) else (1, 0)
        return dx, dy

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

        dx, dy = self._boss_projectile_heading(target)
        distance = (dx**2 + dy**2)**0.5
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
        # Rect stores integer pixels: retain fractional speed in float state,
        # otherwise 4.5 px/tick would silently become 4 px/tick.
        self._precise_x = float(self.rect.x)
        self._precise_y = float(self.rect.y)

    def update(self):
        self.previous_rect = self.rect.copy()
        # Preserve direct rect repositioning by effects/tests.
        if (self.rect.x != round(self._precise_x)
                or self.rect.y != round(self._precise_y)):
            self._precise_x = float(self.rect.x)
            self._precise_y = float(self.rect.y)
        self._precise_x += self.speed * self.direction[0]
        self._precise_y += self.speed * self.direction[1]
        self.rect.x = round(self._precise_x)
        self.rect.y = round(self._precise_y)
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

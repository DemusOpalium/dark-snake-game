import pygame
import random
import time
from config import GRID_SIZE, GRID_WIDTH, GRID_HEIGHT, RED
from modules.graphics import ENEMY_TIM_IMG, ENEMY_SPOONG_IMG, ENEMY_OMNI_IMG, ENEMY_GLUBS_IMG
from modules.enemy_vision import VisionProfile, VisionSensor
from modules.enemy_behavior import (
    BehaviorProfile, permitted_step, movement_intention, reaction_state, STEPS,
)

class NormalEnemy:
    GLIDE_SECONDS = 0.12
    # KI-Test only: spend most of the actual movement interval gliding,
    # instead of visibly jumping after 120ms then waiting at a still frame.
    # Legacy Classic keeps GLIDE_SECONDS unchanged.
    KI_GLIDE_FRACTION = .9
    # An observation only: existing random walk and sprint probability are
    # unchanged until a separately reviewed behaviour PR connects signals.
    SIGHT_PROFILE = VisionProfile(radius_cells=5, fov_degrees=100,
                                  memory_seconds=1.5, scan_interval=0.15)
    BEHAVIOR_PROFILE = BehaviorProfile(
        visible_action="CHASE", chase_speed=2.0,
        search_speed=.9, patrol_speed=1.0,
    )
    # Fixed speed for this *optional* KI pilot; Classic's existing randomly
    # rolled self.speed remains intact and is never overwritten.
    AI_MOVEMENT_SPEED = 1.8
    # This more reactive, longer-distance profile is ONLY active through the
    # existing Admin KI-Test. Classic without KI-Test keeps the old eyes and
    # random sprint behavior verbatim.
    AI_SIGHT_PROFILE = VisionProfile(
        radius_cells=8, fov_degrees=150,
        memory_seconds=4.0, scan_interval=.05,
        alert_radius_cells=16, reaction_seconds=.05,
    )

    def __init__(self):
        self.x = random.randint(0, GRID_WIDTH - 1)
        self.y = random.randint(0, GRID_HEIGHT - 1)
        self.spawn_time = time.time()
        self.speed = random.uniform(0.5, 1.5)
        self.health = random.randint(1, 3)
        self.last_move = time.time()
        self._frame_time = self.last_move
        self._render_start = self._render_target = (self.x, self.y)
        self._glide_duration = 0
        self.sprint_chance = 0.05
        self.sprint_speed_multiplier = 3
        self.sprint_duration = 0.5
        self.sprint_active = False
        self.sprint_end_time = 0
        self.facing = (1, 0)
        self.eyes = VisionSensor(self.SIGHT_PROFILE)
        # Developer-only pilot, off by default: preserves Classic random walk.
        self.behavior_enabled = False
        self.behavior_state = "PATROL"
        self.behavior_profile = self.BEHAVIOR_PROFILE
        self.navigation_blockers = frozenset()

        self.image = random.choice([ENEMY_TIM_IMG, ENEMY_SPOONG_IMG, ENEMY_OMNI_IMG, ENEMY_GLUBS_IMG])
        if self.image:
            size = random.choice([GRID_SIZE, int(GRID_SIZE * 1.5)])
            self.image = pygame.transform.scale(self.image, (size, size))
            self.width, self.height = self.image.get_size()
        else:
            self.width = self.height = GRID_SIZE

    def set_ai_preview(self, enabled: bool):
        """Swap sight profile once per Admin toggle, never once per frame."""
        enabled = bool(enabled)
        if enabled != self.behavior_enabled:
            self.behavior_enabled = enabled
            self.behavior_state = "PATROL"
            self.eyes.profile = (
                self.AI_SIGHT_PROFILE if enabled else self.SIGHT_PROFILE
            )
            self.eyes.reset()

    def _start_sprint(self, now, duration, player_x, player_y):
        self.sprint_active = True
        self.sprint_end_time = now + duration
        if player_x is not None and player_y is not None:
            dx = 1 if player_x > self.x else -1 if player_x < self.x else 0
            dy = 1 if player_y > self.y else -1 if player_y < self.y else 0
            self.sprint_dir = (dx, dy)
        else:
            self.sprint_dir = (random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))

    def update(self, player_x=None, player_y=None, *, movement_factor=1.0):
        current_time = self._frame_time = time.time()
        if self.behavior_enabled:
            self.behavior_state = reaction_state(
                self.eyes.result, (self.x, self.y), self.behavior_profile,
            )
        else:
            self.behavior_state = "PATROL"
        if (not self.behavior_enabled and not self.sprint_active
                and random.random() < self.sprint_chance):
            self._start_sprint(current_time, self.sprint_duration, player_x, player_y)

        # The old random base-speed range (0.5–1.5) made the new AI appear
        # inexplicably sluggish. For KI-Test only, every instance of this
        # enemy type uses a fixed, tunable base speed from its class profile.
        # Old Classic without KI-Test retains self.speed *all the way through*.
        base_speed = self.AI_MOVEMENT_SPEED if self.behavior_enabled else self.speed
        current_speed = base_speed * (self.sprint_speed_multiplier if self.sprint_active else 1)
        if self.behavior_enabled and not self.sprint_active:
            if self.behavior_state in ("CHASE", "RETREAT"):
                current_speed *= self.behavior_profile.chase_speed
            elif self.behavior_state == "SEARCH":
                current_speed *= self.behavior_profile.search_speed
            elif self.behavior_state == "PATROL":
                current_speed *= self.behavior_profile.patrol_speed
        current_speed *= movement_factor
        interval = 1.0 / current_speed
        if current_time - self.last_move >= interval:
            # When alert/search tempo changes, the next step may begin before
            # the previous glide finishes. Continue from the *drawn* position
            # rather than snapping back to the previous logical grid cell.
            render_start = (self._interpolated_grid_position()
                            if self.behavior_enabled else (self.x, self.y))
            self.last_move = current_time
            if self.sprint_active:
                dx, dy = self.sprint_dir
            elif self.behavior_enabled:
                reading = self.eyes.result
                if (self.behavior_state in ("CHASE", "SEARCH", "RETREAT")
                        and reading.last_known_cell is not None):
                    dx, dy = movement_intention(
                        (self.x, self.y), reading.last_known_cell,
                        self.behavior_state, self.navigation_blockers,
                        (GRID_WIDTH, GRID_HEIGHT),
                    )
                elif self.behavior_state == "GUARD":
                    dx = dy = 0
                else:
                    # Keep the original patrol's random quality, but constrain
                    # candidate moves to authored solid sight barriers.
                    valid = [(0, 0)] + [
                        step for step in STEPS if permitted_step(
                            (self.x, self.y), step, self.navigation_blockers,
                            (GRID_WIDTH, GRID_HEIGHT),
                        )
                    ]
                    dx, dy = random.choice(valid)
            else:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
            if self.behavior_enabled and not permitted_step(
                    (self.x, self.y), (dx, dy), self.navigation_blockers,
                    (GRID_WIDTH, GRID_HEIGHT)):
                dx = dy = 0
            self._render_start = render_start
            self.x = max(0, min(self.x + dx, GRID_WIDTH - 1))
            self.y = max(0, min(self.y + dy, GRID_HEIGHT - 1))
            # Use actual movement rather than a speculative/random facing.
            direction = (self.x - self._render_start[0],
                         self.y - self._render_start[1])
            if direction != (0, 0):
                self.facing = direction
            self._render_target = (self.x, self.y)
            self._glide_duration = (
                interval * self.KI_GLIDE_FRACTION if self.behavior_enabled
                else min(self.GLIDE_SECONDS, interval)
            )
        if self.sprint_active and current_time >= self.sprint_end_time:
            self.sprint_active = False

    def draw(self, screen):
        rect = self.get_render_rect()
        if self.image:
            screen.blit(self.image, rect)
        else:
            pygame.draw.rect(screen, RED, rect)

    def _interpolated_grid_position(self):
        """Return the per-frame displayed position in grid units.

        The authoritative enemy grid cell stays integral. Both sprite and
        collision rectangle use the same sample; this is not a second AI.
        """
        x, y = self.x, self.y
        elapsed = self._frame_time - self.last_move
        if self._render_target == (x, y) and 0 <= elapsed < self._glide_duration:
            alpha = elapsed / self._glide_duration
            start_x, start_y = self._render_start
            x, y = start_x + (x - start_x) * alpha, start_y + (y - start_y) * alpha
        return x, y

    def get_render_rect(self):
        # One simulation frame-time feeds both sprite and collision queries.
        x, y = self._interpolated_grid_position()
        return pygame.Rect(round(x * GRID_SIZE), round(y * GRID_SIZE),
                           self.width, self.height)

    def get_hitbox(self):
        """Rectangular collision area matching the scaled enemy sprite."""
        return self.get_render_rect()

    def get_rect(self):
        """Compatibility alias for older callers."""
        return self.get_hitbox()

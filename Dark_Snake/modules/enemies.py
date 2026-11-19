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
    # An observation only: existing random walk and sprint probability are
    # unchanged until a separately reviewed behaviour PR connects signals.
    SIGHT_PROFILE = VisionProfile(radius_cells=5, fov_degrees=100,
                                  memory_seconds=1.5, scan_interval=0.15)
    BEHAVIOR_PROFILE = BehaviorProfile(visible_action="CHASE")

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

        current_speed = self.speed * (self.sprint_speed_multiplier if self.sprint_active else 1)
        if self.behavior_enabled and not self.sprint_active and self.behavior_state in (
                "CHASE", "RETREAT", "SEARCH"):
            current_speed *= self.behavior_profile.chase_speed
        current_speed *= movement_factor
        interval = 1.0 / current_speed
        if current_time - self.last_move >= interval:
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
            self._render_start = (self.x, self.y)
            self.x = max(0, min(self.x + dx, GRID_WIDTH - 1))
            self.y = max(0, min(self.y + dy, GRID_HEIGHT - 1))
            # Use actual movement rather than a speculative/random facing.
            direction = (self.x - self._render_start[0],
                         self.y - self._render_start[1])
            if direction != (0, 0):
                self.facing = direction
            self._render_target = (self.x, self.y)
            self._glide_duration = min(self.GLIDE_SECONDS, interval)
        if self.sprint_active and current_time >= self.sprint_end_time:
            self.sprint_active = False

    def draw(self, screen):
        rect = self.get_render_rect()
        if self.image:
            screen.blit(self.image, rect)
        else:
            pygame.draw.rect(screen, RED, rect)

    def get_render_rect(self):
        # Sample once per update so the sprite and collision queries agree in a frame.
        x, y = self.x, self.y
        elapsed = self._frame_time - self.last_move
        if self._render_target == (x, y) and 0 <= elapsed < self._glide_duration:
            alpha = elapsed / self._glide_duration
            start_x, start_y = self._render_start
            x, y = start_x + (x - start_x) * alpha, start_y + (y - start_y) * alpha
        return pygame.Rect(round(x * GRID_SIZE), round(y * GRID_SIZE), self.width, self.height)

    def get_hitbox(self):
        """Rectangular collision area matching the scaled enemy sprite."""
        return self.get_render_rect()

    def get_rect(self):
        """Compatibility alias for older callers."""
        return self.get_hitbox()

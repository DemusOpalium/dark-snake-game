import pygame
import random
import time
from config import GRID_SIZE, GRID_WIDTH, GRID_HEIGHT, RED
from modules.graphics import ENEMY_TIM_IMG, ENEMY_SPOONG_IMG, ENEMY_OMNI_IMG, ENEMY_GLUBS_IMG

class NormalEnemy:
    GLIDE_SECONDS = 0.12

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

    def update(self, player_x=None, player_y=None):
        current_time = self._frame_time = time.time()
        if not self.sprint_active and random.random() < self.sprint_chance:
            self._start_sprint(current_time, self.sprint_duration, player_x, player_y)

        current_speed = self.speed * (self.sprint_speed_multiplier if self.sprint_active else 1)
        interval = 1.0 / current_speed
        if current_time - self.last_move >= interval:
            self.last_move = current_time
            if self.sprint_active:
                dx, dy = self.sprint_dir
            else:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
            self._render_start = (self.x, self.y)
            self.x = max(0, min(self.x + dx, GRID_WIDTH - 1))
            self.y = max(0, min(self.y + dy, GRID_HEIGHT - 1))
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

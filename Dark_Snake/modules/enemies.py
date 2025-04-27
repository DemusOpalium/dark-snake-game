import pygame
import random
import time
from config import GRID_SIZE, GRID_WIDTH, GRID_HEIGHT, RED
from modules.graphics import ENEMY_TIM_IMG, ENEMY_SPOONG_IMG, ENEMY_OMNI_IMG, ENEMY_GLUBS_IMG

class NormalEnemy:
    def __init__(self):
        self.x = random.randint(0, GRID_WIDTH - 1)
        self.y = random.randint(0, GRID_HEIGHT - 1)
        self.spawn_time = time.time()
        self.speed = random.uniform(0.5, 1.5)
        self.health = random.randint(1, 3)
        self.last_move = time.time()
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

    def update(self, player_x=None, player_y=None):
        current_time = time.time()
        if not self.sprint_active and random.random() < self.sprint_chance:
            self.sprint_active = True
            self.sprint_end_time = current_time + self.sprint_duration
            if player_x is not None and player_y is not None:
                dx = 1 if player_x > self.x else -1 if player_x < self.x else 0
                dy = 1 if player_y > self.y else -1 if player_y < self.y else 0
                self.sprint_dir = (dx, dy)
            else:
                self.sprint_dir = (random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))

        current_speed = self.speed * (self.sprint_speed_multiplier if self.sprint_active else 1)
        interval = 1.0 / current_speed
        if current_time - self.last_move >= interval:
            self.last_move = current_time
            if self.sprint_active:
                dx, dy = self.sprint_dir
            else:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
            self.x = max(0, min(self.x + dx, GRID_WIDTH - 1))
            self.y = max(0, min(self.y + dy, GRID_HEIGHT - 1))
        if self.sprint_active and current_time >= self.sprint_end_time:
            self.sprint_active = False

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.x * GRID_SIZE, self.y * GRID_SIZE))
        else:
            pygame.draw.rect(screen, RED, (self.x * GRID_SIZE, self.y * GRID_SIZE, GRID_SIZE, GRID_SIZE))

    def get_rect(self):
        return pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, self.width, self.height)

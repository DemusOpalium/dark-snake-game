# modules/enemies.py
import pygame, random, time
from config import GRID_SIZE, GRID_WIDTH, GRID_HEIGHT, WHITE, RED, DARK_GREY
from modules.graphics import ENEMY_TIM_IMG, ENEMY_SPOONG_IMG, ENEMY_OMNI_IMG, ENEMY_GLUBS_IMG

class NormalEnemy:
    def __init__(self):
        # Position zufällig innerhalb des Spielfelds
        self.x = random.randint(0, GRID_WIDTH - 1)
        self.y = random.randint(0, GRID_HEIGHT - 1)
        # Standardgeschwindigkeit
        self.speed = random.uniform(0.5, 1.5)
        self.last_move = time.time()
        self.move_interval = 1.0 / self.speed
        # Gesundheit (z. B. 1-3 Treffer)
        self.health = random.randint(1, 3)
        # Wähle ein zufälliges Bild für diesen Gegner
        self.image = random.choice([ENEMY_TIM_IMG, ENEMY_SPOONG_IMG, ENEMY_OMNI_IMG, ENEMY_GLUBS_IMG])
        if self.image:
            # Skalieren auf 40x40 oder 60x60 (zufällig)
            size = random.choice([40, 60])
            self.image = pygame.transform.scale(self.image, (size, size))
            self.width, self.height = self.image.get_size()
        else:
            self.width = self.height = GRID_SIZE
        # Sprint-Attribute: Bei einer Chance wird der Gegner einen Sprint ausführen
        self.sprint_chance = 0.05  # 5% Chance, pro Update
        self.sprint_speed_multiplier = 3  # Erhöhte Geschwindigkeit im Sprint
        self.sprint_duration = 0.5  # Dauer des Sprints in Sekunden
        self.sprint_active = False
        self.sprint_end_time = 0

    def update(self, player_x=None, player_y=None):
        current_time = time.time()
        # Möglicher Sprint-Start (nur, wenn nicht schon aktiv)
        if not self.sprint_active and random.random() < self.sprint_chance:
            self.sprint_active = True
            self.sprint_end_time = current_time + self.sprint_duration
            # Falls Spielerposition bekannt, wähle zufällig Richtung: zum Spieler oder weg von ihm
            if player_x is not None and player_y is not None:
                if random.choice([True, False]):
                    # In Richtung des Spielers
                    dx = 1 if player_x > self.x else -1
                    dy = 1 if player_y > self.y else -1
                else:
                    # Vom Spieler weg
                    dx = -1 if player_x > self.x else 1
                    dy = -1 if player_y > self.y else 1
                self.sprint_dir = (dx, dy)
            else:
                self.sprint_dir = (random.choice([-1,0,1]), random.choice([-1,0,1]))

        # Wähle die Geschwindigkeit (normal oder Sprint)
        current_speed = self.speed * (self.sprint_speed_multiplier if self.sprint_active else 1)
        interval = 1.0 / current_speed
        if current_time - self.last_move >= interval:
            self.last_move = current_time
            # Wenn Sprint aktiv, benutze Sprint-Richtung
            if self.sprint_active:
                dx, dy = self.sprint_dir
            else:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
            self.x = max(0, min(self.x + dx, GRID_WIDTH - 1))
            self.y = max(0, min(self.y + dy, GRID_HEIGHT - 1))
        # Deaktiviere Sprint, falls Zeit abgelaufen
        if self.sprint_active and current_time >= self.sprint_end_time:
            self.sprint_active = False

    def draw(self, screen):
        if self.image:
            screen.blit(self.image, (self.x * GRID_SIZE, self.y * GRID_SIZE))
        else:
            pygame.draw.rect(screen, RED, (self.x * GRID_SIZE, self.y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
            
    def get_rect(self):
        # Nutze die Bildgröße, wenn vorhanden
        return pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, self.width, self.height)


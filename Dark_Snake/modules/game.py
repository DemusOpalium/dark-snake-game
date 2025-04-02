# modules/game.py
import pygame, sys, random, time, os
from math import sqrt, atan2, cos, sin
from modules.enums import GameState, Direction, ItemType
from config import (WINDOW_WIDTH, WINDOW_HEIGHT, GRID_SIZE, FPS, GRID_WIDTH, GRID_HEIGHT,
                    DARK_GREY, WHITE, GREEN, RED, PURPLE, ORANGE, GOLDEN, LEADERBOARD_FILE,
                    START_SPEED, MAX_SPEED)
from modules.graphics import (
    SNAKE_HEAD_IMG, SNAKE_HEAD1G20, SNAKE_HEAD2G20, SNAKE_HEAD3G20,
    SNAKE_HEAD_BETA, SNAKE_BODY_IMG, SNAKE_BODY_BETA, SNAKE_BODY_Body7,
    SNAKE_BODY_Body5, SNAKE_BODY_Body4, SNAKE_BODY_Body2, SNAKE_BODY_Body6,
    PROJECTILE_IMG, TITLE_IMG, BOSS_IMG, BOSS_ALT_IMG, PORTAL_IMAGES, ITEM_IMAGES,
    OPTIONS_BUTTON_IMG, PLAY_BUTTON_IMG
)
from modules.audio import SOUNDS
from modules.ui import Button, Slider, CheckBox
from modules.controls import ControlsMenu
from modules.customization import CustomizationMenu
from modules.enemies import NormalEnemy

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
    r, g, b = random.randint(0,255), random.randint(0,255), random.randint(0,255)
    return (r, g, b)

def get_aoe_effect():
    spell_files = ["Spellgreen1G60.png", "SpellOrangeG60.png", "Spellwhite2G60.png"]
    images = []
    for fname in spell_files:
        path = os.path.join("assets", "graphics", fname)
        try:
            img = pygame.image.load(path).convert_alpha()
            images.append(img)
        except Exception as e:
            print(f"Fehler beim Laden von {fname}: {e}")
    if images:
        return random.choice(images)
    return None

# ---------------------------
# Boss-Klasse 1
# ---------------------------
class Boss:
    def __init__(self, level):
        self.x = random.randint(5, GRID_WIDTH - 5)
        self.y = random.randint(5, GRID_HEIGHT - 5)
        self.size = 3 + level // 2
        # Boss hat mindestens genügend Leben (mind. 30 Treffer)
        self.health = max(30, 3 + level * 5)
        self.speed = 1 + level * 0.2 + random.uniform(0, 0.5)
        self.last_move = time.time()
        self.chase_speed = 0.5
        self.attack_mode = "normal"
        # Zufällige Boss-Grafik aus mehreren Dateien:
        boss_files = ["Boss-AlexG60.png", "Boss-BolgiG60.png", "Boss-DemusG60.png", 
                      "Boss-FinG60.png", "Boss-GlobyG60.png", "Boss-NeoG60.png", 
                      "Boss-RingG60.png", "Boss-SkullPurPurG60.png"]
        self.image = None
        # Wähle zufällig einen Boss
        fname = random.choice(boss_files)
        # Für Boss-DemusG60: Lade Animation aus Ordner Boss001 (frame0000.png bis frame0048.png)
        if fname == "Boss-DemusG60.png":
            self.frames = []
            self.current_frame = 0
            self.last_frame_time = time.time()
            folder = os.path.join("assets", "graphics", "Boss001")
            for i in range(49):  # 0 bis 48
                frame_filename = os.path.join(folder, f"frame{i:04d}.png")
                try:
                    img = pygame.image.load(frame_filename).convert_alpha()
                    # Optional: Skalieren auf 60x60 Pixel (anpassen falls benötigt)
                    img = pygame.transform.scale(img, (60, 60))
                    self.frames.append(img)
                except Exception as e:
                    print(f"Fehler beim Laden von {frame_filename}: {e}")
            if self.frames:
                self.image = self.frames[0]
        # Für Boss-RingG60: Lade Animation aus Ordner Boss002 (frame0000.png bis frame0014.png)
        elif fname == "Boss-RingG60.png":
            self.frames = []
            self.current_frame = 0
            self.last_frame_time = time.time()
            folder = os.path.join("assets", "graphics", "Boss002")
            for i in range(15):  # 0 bis 14
                frame_filename = os.path.join(folder, f"frame{i:04d}.png")
                try:
                    img = pygame.image.load(frame_filename).convert_alpha()
                    img = pygame.transform.scale(img, (60, 60))
                    self.frames.append(img)
                except Exception as e:
                    print(f"Fehler beim Laden von {frame_filename}: {e}")
            if self.frames:
                self.image = self.frames[0]
                        # Für Boss-FinG60: Lade Animation aus Ordner Boss-FinG60.png (frame0000.png bis frame0026.png)
        elif fname == "Boss-FinG60.png":
            self.frames = []
            self.current_frame = 0
            self.last_frame_time = time.time()
            folder = os.path.join("assets", "graphics", "Boss003")
            for i in range(15):  # 0 bis 26
                frame_filename = os.path.join(folder, f"frame{i:04d}.png")
                try:
                    img = pygame.image.load(frame_filename).convert_alpha()
                    img = pygame.transform.scale(img, (60, 60))
                    self.frames.append(img)
                except Exception as e:
                    print(f"Fehler beim Laden von {frame_filename}: {e}")
            if self.frames:
                self.image = self.frames[0]
        else:
            # Für alle anderen Boss-Bilder: Lade das Einzelbild
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
        # Falls Animationsframes vorhanden sind, aktualisiere den aktuellen Frame
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
            return "aoe"
        if current_time >= self.next_proj:
            self.next_proj = current_time + 3
            return "boss_shoot"
        return None

    def update_animation(self, current_time):
        # Wechsel den Frame alle 0.1 Sekunden – anpassen, falls nötig
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
        # Lebensbalken über dem Boss
        bar_width = self.size * GRID_SIZE
        bar_height = 5
        life_ratio = self.health / max(30, 3 + self.health)
        life_bar = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE - 10,
                               int(bar_width * life_ratio), bar_height)
        pygame.draw.rect(screen, GREEN, life_bar)
        pygame.draw.rect(screen, WHITE, (self.x * GRID_SIZE, self.y * GRID_SIZE - 10,
                                         bar_width, bar_height), 1)
        # AOE-Effekt anzeigen
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
        if self.image:
            return pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE,
                               self.image.get_width(), self.image.get_height())
        return pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE,
                           self.size * GRID_SIZE, self.size * GRID_SIZE)

    def take_damage(self):
        self.health -= 1
        if SOUNDS.get("powerup"):
            SOUNDS["powerup"].play()
        return self.health <= 0

# Boss-Klasse 2 (Erbt von Boss)
class Boss2(Boss):
    def __init__(self, level):
        super().__init__(level)
        self.size = 4 + level // 2
        self.health = max(30, 5 + level * 5)
        self.speed = 1 + level * 0.25 + random.uniform(0, 0.5)
        self.chase_speed = 0.4
        self.attack_mode = "shield"
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

# Portal-Klasse (Kollisionsbox 40x40)
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

# Item-Klasse
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
                pygame.draw.circle(screen, PURPLE, (self.x * GRID_SIZE + GRID_SIZE//2, self.y * GRID_SIZE + GRID_SIZE//2), GRID_SIZE//2)
            elif self.type == ItemType.PROJECTILE_SHOOT:
                pygame.draw.circle(screen, (0,255,255), (self.x * GRID_SIZE + GRID_SIZE//2, self.y * GRID_SIZE + GRID_SIZE//2), GRID_SIZE//2)
            else:
                pygame.draw.circle(screen, RED, (self.x * GRID_SIZE + GRID_SIZE//2, self.y * GRID_SIZE + GRID_SIZE//2), GRID_SIZE//2)

# Importiere weitere Module
from modules.enemies import NormalEnemy
from modules.controls import ControlsMenu
from modules.customization import CustomizationMenu
from modules.audio import get_music_library, play_background_music, set_music_volume

# Zunächst: Dropdown-Klasse definieren
class Dropdown:
    def __init__(self, x, y, width, height, options, current_option, font, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = options.index(current_option) if current_option in options else 0
        self.font = font
        self.callback = callback
        self.expanded = False

    def draw(self, surface):
        # Zeichne das Auswahlfeld
        pygame.draw.rect(surface, DARK_GREY, self.rect)
        text = self.font.render(self.options[self.selected_index], True, WHITE)
        surface.blit(text, (self.rect.x + 5, self.rect.y + 5))
        # Zeichne Pfeil
        pygame.draw.polygon(surface, WHITE, [
            (self.rect.right - 15, self.rect.y + 10),
            (self.rect.right - 5, self.rect.y + 10),
            (self.rect.right - 10, self.rect.y + 20)
        ])
        # Falls erweitert, zeige alle Optionen an
        if self.expanded:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                pygame.draw.rect(surface, DARK_GREY, option_rect)
                opt_text = self.font.render(option, True, WHITE)
                surface.blit(opt_text, (option_rect.x + 5, option_rect.y + 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            # Klickt auf das Hauptfeld? Dann umschalten
            if self.rect.collidepoint(mouse_pos):
                self.expanded = not self.expanded
            elif self.expanded:
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                    if option_rect.collidepoint(mouse_pos):
                        self.selected_index = i
                        self.expanded = False
                        self.callback(option)
                        break
                else:
                    self.expanded = False

# In der Game-Klasse (Hauptspielklasse)
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
            'music_volume': 0.5,       # Für SFX oder andere Effekte
            'sfx_volume': 0.7,
            'bg_music_volume': 0.5,    # NEU: Hintergrundmusik-Lautstärke
            'difficulty': 1.0,
            'field_scale': 1.0,
            'snake_design': 0,
            'custom_head': None
        }
        self.player_count = 1
        self.create_ui_elements()
        self.reset_game()
        # Titelbild-Hintergrund: Brauner Holzhintergrund
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
        self.effects = {
            'speed_boost': 0,
            'speed_reduction': 0,
            'score_boost': 0,
            'invincibility': 0,
            'length_shortener': 0,
            'length_double': 0,
            'projectile_shoot': 0  # Multi-Shoot-Effekt
        }
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
        self.portal_effect_active = False
        self.portal_effect_end = 0
        self.portal_effect_type = None
        self.portal_spawn_cooldown = 0
        self.projectiles = []
        self.achievement_messages = []
        self.enemies = []
        self.controls_menu = ControlsMenu(self)
        self.custom_menu = None
        self.game_state = GameState.INTRO
        # Steuerung im Einzelspieler-Modus: Erlaubt WASD und Pfeiltasten
        self.next_direction = Direction.RIGHT
        self.snake_direction = Direction.RIGHT
        self.last_auto_shoot = time.time()
        self.extra_auto_shots = 0

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

    def create_ui_elements(self):
        center_x = WINDOW_WIDTH // 2
        button_width = 200
        button_height = 60

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
        self.pause_buttons = [
            Button(center_x - 100, WINDOW_HEIGHT // 2, button_width, button_height, "PAUSE",
                   action=lambda: self.set_state(GameState.PAUSE)),
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 80, button_width, button_height, "HAUPTMENÜ",
                   color=PURPLE, action=lambda: self.confirm_back_to_main()),
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 160, button_width, button_height, "BEENDEN",
                   color=RED, action=lambda: sys.exit())
        ]
        self.game_over_buttons = [
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 100, button_width, button_height, "NEUSTART",
                   action=lambda: self.reset_game()),
            Button(center_x - 100, WINDOW_HEIGHT // 2 + 180, button_width, button_height, "HAUPTMENÜ",
                   color=PURPLE, action=lambda: self.confirm_back_to_main())
        ]
        slider_width = 300
        slider_height = 20
        slider_x = center_x - slider_width // 2
        self.settings_elements = [
            Slider(slider_x, 200, slider_width, slider_height, 1, 15, self.settings['initial_speed'], "Geschwindigkeit"),
            Slider(slider_x, 230, slider_width, slider_height, 0.5, 2.0, self.settings['difficulty'], "Schwierigkeitsgrad"),
            Slider(slider_x, 260, slider_width, slider_height, 0, 1, self.settings['music_volume'], "Musik"),
            Slider(slider_x, 290, slider_width, slider_height, 0, 1, self.settings['sfx_volume'], "Effekte"),
            CheckBox(slider_x, 320, 20, "Vollbild", self.settings['fullscreen']),
            Slider(slider_x, 350, slider_width, slider_height, 0.5, 2.0, self.settings['field_scale'], "Spielfeld"),
            Slider(slider_x, 380, slider_width, slider_height, 0, 1, self.settings['snake_design'], "Schlangendesign"),
            Button(center_x - 100, WINDOW_HEIGHT - 150, 200, 60, "SPEICHERN", action=lambda: self.save_settings()),
            Button(center_x - 100, WINDOW_HEIGHT - 80, 200, 60, "CHARAKTER", action=self.open_customization, color=PURPLE)
        ]
        # NEU: Dropdown für Hintergrundmusik
        music_options = get_music_library()  # Musikoptionen aus dem Musikordner laden
        if not music_options:
            music_options = ["Default"]
        font = pygame.font.SysFont('Arial', 20)
        self.bg_music_dropdown = Dropdown(slider_x, 410, slider_width, slider_height, music_options, music_options[0], font, self.change_bg_music)

    def open_customization(self):
        self.set_state(GameState.CUSTOMIZATION)
        self.custom_menu = CustomizationMenu(self)

    # SAVE_SETTINGS: Speichert die aktuellen Einstellungen
    def save_settings(self):
        with open("settings.txt", "w") as f:
            for key, value in self.settings.items():
                f.write(f"{key}={value}\n")
        print("Einstellungen wurden gespeichert!")
        # Hintergrundmusik-Lautstärke setzen
        set_music_volume(self.settings['bg_music_volume'])

    def change_bg_music(self, selected_option):
        print(f"Hintergrundmusik geändert: {selected_option}")
        play_background_music(selected_option, self.settings['bg_music_volume'])

    def start_game(self, players):
        self.player_count = players
        self.reset_game()
        self.set_state(GameState.GAME)

    def confirm_back_to_main(self):
        if self.show_confirmation("Zum Hauptmenü?"):
            self.set_state(self.intro_state())

    def show_confirmation(self, message):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        msg = pygame.font.SysFont('Comic Sans MS', 30).render(message, True, WHITE)
        self.screen.blit(msg, (WINDOW_WIDTH//2 - msg.get_width()//2, WINDOW_HEIGHT//2 - msg.get_height()//2))
        pygame.display.update()
        time.sleep(2)
        return True

    def set_state(self, state):
        self.game_state = state
        if state == GameState.GAME:
            self.last_update_time = time.time()

    def reset_game(self):
        self.leaderboard_mode = False
        self.name_input = ""
        self.set_state(self.intro_state())
        if self.player_count == 2:
            self.snake1 = [(GRID_WIDTH//2, GRID_HEIGHT//2)]
            self.snake2 = [(GRID_WIDTH//2, GRID_HEIGHT//2 + 2)]
            self.snake_direction1 = Direction.RIGHT
            self.snake_direction2 = Direction.RIGHT
            self.next_direction1 = Direction.RIGHT
            self.next_direction2 = Direction.RIGHT
        else:
            self.snake = [(GRID_WIDTH//2, GRID_HEIGHT//2)]
            self.snake_direction = Direction.RIGHT
            self.next_direction = Direction.RIGHT
        self.items = []
        self.spawn_food()
        self.score = 0
        self.level = 1
        self.experience = 0
        self.exp_to_next_level = 100
        self.speed = self.settings['initial_speed']
        self.last_update_time = time.time()
        self.effects = {
            'speed_boost': 0,
            'speed_reduction': 0,
            'score_boost': 0,
            'invincibility': 0,
            'length_shortener': 0,
            'length_double': 0,
            'projectile_shoot': 0
        }
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
        self.portal_spawn_cooldown = 0
        self.projectiles = []
        self.achievement_messages = []
        self.enemies = []
        self.last_auto_shoot = time.time()
        self.extra_auto_shots = 0

    def spawn_food(self):
        while True:
            new_item = Item(ItemType.FOOD)
            occ = (self.snake1 + self.snake2) if self.player_count == 2 else self.snake
            if (new_item.x, new_item.y) not in occ and not any(item.x == new_item.x and item.y == new_item.y for item in self.items):
                self.items.append(new_item)
                break

    def spawn_new_item(self):
        chance = random.random()
        if chance < 0.5:
            itype = ItemType.FOOD
        elif chance < 0.6:
            itype = ItemType.SPEED_BOOST
        elif chance < 0.7:
            itype = ItemType.SPEED_REDUCTION
        elif chance < 0.75:
            itype = ItemType.SCORE_BOOST
        elif chance < 0.8:
            itype = ItemType.INVINCIBILITY
        elif chance < 0.83:
            itype = ItemType.LENGTH_SHORTENER
        elif chance < 0.86:
            itype = ItemType.LENGTH_DOUBLE
        elif chance < 0.90:
            itype = ItemType.LOOT_BOX
        elif chance < 0.98:
            itype = ItemType.DICE_EVENT
        else:
            itype = ItemType.SPECIAL_DAMAGE
        while True:
            new_item = Item(itype)
            occ = (self.snake1 + self.snake2) if self.player_count == 2 else self.snake
            if (new_item.x, new_item.y) not in occ and not any(item.x == new_item.x and item.y == new_item.y for item in self.items):
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
        self.boss = boss_class(self.level)
        self.items.append(Item(ItemType.PROJECTILE_SHOOT))
        self.add_achievement(self.boss.announcement)
        self.game_state = GameState.BOSS_FIGHT

    def add_achievement(self, message):
        self.achievement_messages.append((message, time.time() + 10))

    def activate_portal(self, event):
        self.portal_effect_active = True
        self.portal_effect_end = time.time() + 60
        self.portal_spawn_cooldown = time.time() + 300
        self.background.fill((random.randint(0,50), random.randint(0,50), random.randint(0,50)))
        for i in range(0, WINDOW_WIDTH, GRID_SIZE*2):
            for j in range(0, WINDOW_HEIGHT, GRID_SIZE*2):
                pygame.draw.rect(self.background, (random.randint(10,30), random.randint(10,30), random.randint(10,30)),
                                 (i, j, GRID_SIZE, GRID_SIZE))
        self.intro_bg = self.menu_bg.copy()
        if event == "teleport":
            if self.player_count == 2:
                self.snake1[0] = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
                self.snake2[0] = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
            else:
                self.snake[0] = (random.randint(0, GRID_WIDTH-1), random.randint(0, GRID_HEIGHT-1))
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

    def update_projectiles(self):
        current_time = time.time()
        new_proj = []
        for proj in self.projectiles:
            dx, dy = proj['dir']
            new_x = proj['pos'][0] + dx
            new_y = proj['pos'][1] + dy
            proj['pos'] = (new_x, new_y)
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                continue
            proj_rect = pygame.Rect(new_x * GRID_SIZE, new_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if self.boss and self.boss.get_rect().colliderect(proj_rect):
                self.boss.health -= 10
                if self.boss.health <= 0:
                    self.boss = None
                    self.game_state = GameState.GAME
                    self.boss_spawn_timer = current_time + 60 + random.randint(0,30)
                    self.score += 100 * self.level
                    self.add_achievement("Boss besiegt! Boss Down Easy Going !!")
                    self.effects['boss_loot'] = current_time + 10
                continue
            target = self.snake1[0] if self.player_count == 2 and self.snake1 else (self.snake[0] if self.snake else None)
            if target:
                head_rect = pygame.Rect(target[0] * GRID_SIZE, target[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if head_rect.colliderect(proj_rect):
                    # Eigene Projektile verursachen keinen Schaden
                    continue
            new_proj.append(proj)
        self.projectiles = new_proj

    def check_boss_collision(self, snake_head):
        if self.boss:
            boss_rect = self.boss.get_rect()
            head_x = snake_head[0] * GRID_SIZE + GRID_SIZE//2
            head_y = snake_head[1] * GRID_SIZE + GRID_SIZE//2
            return boss_rect.collidepoint(head_x, head_y)
        return False

    def auto_shoot(self):
        current_time = time.time()
        if current_time - self.last_auto_shoot >= 3:
            self.last_auto_shoot = current_time
            # Bestimme den Schuss-Kopf (Einzelspieler: self.snake[0], sonst: self.snake1[0])
            head = None
            if self.player_count == 1 and self.snake:
                head = self.snake[0]
            elif self.player_count == 2 and self.snake1:
                head = self.snake1[0]
            if head is None:
                return
            target = None
            min_dist = float("inf")
            # Auto-Aim: Suche den nächsten Gegner
            if self.enemies:
                for enemy in self.enemies:
                    dist = sqrt((head[0] - enemy.x) ** 2 + (head[1] - enemy.y) ** 2)
                    if dist < min_dist:
                        min_dist = dist
                        target = enemy
            if target:
                dx = target.x - head[0]
                dy = target.y - head[1]
                angle = atan2(dy, dx)
                dir_x = cos(angle) * 2
                dir_y = sin(angle) * 2
            else:
                if self.player_count == 1:
                    dir_x, dir_y = self.snake_direction.value[0] * 2, self.snake_direction.value[1] * 2
                else:
                    dir_x, dir_y = self.snake_direction1.value[0] * 2, self.snake_direction1.value[1] * 2
            proj = {'pos': (head[0], head[1]),
                    'dir': (dir_x, dir_y),
                    "effect": "damage"}
            self.projectiles.append(proj)
            # Zusätzliche Auto-Shoot-Projektile (extra Items, maximal +6)
            for _ in range(self.extra_auto_shots):
                deviation = random.uniform(-0.3, 0.3)
                proj_extra = {'pos': (head[0], head[1]),
                              'dir': (dir_x + deviation, dir_y + deviation),
                              "effect": "damage"}
                self.projectiles.append(proj_extra)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button != 1:
                continue
            elif event.type == pygame.KEYDOWN:
                # Im Spielmodus: Auto-Shoot ist aktiv, also nur Steuerung ändern
                if self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.set_state(GameState.PAUSE)
                    # Einzelspieler: Erlaubt WASD und Pfeiltasten
                    if self.player_count == 1:
                        if event.key in (pygame.K_UP, pygame.K_w) and self.snake_direction != Direction.DOWN:
                            self.next_direction = Direction.UP
                        elif event.key in (pygame.K_DOWN, pygame.K_s) and self.snake_direction != Direction.UP:
                            self.next_direction = Direction.DOWN
                        elif event.key in (pygame.K_LEFT, pygame.K_a) and self.snake_direction != Direction.RIGHT:
                            self.next_direction = Direction.LEFT
                        elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.snake_direction != Direction.LEFT:
                            self.next_direction = Direction.RIGHT
                    # Zweispielermodus:
                    elif self.player_count == 2:
                        # Spieler 1 steuert mit WASD
                        if event.key in (pygame.K_w) and self.snake_direction1 != Direction.DOWN:
                            self.next_direction1 = Direction.UP
                        elif event.key in (pygame.K_s) and self.snake_direction1 != Direction.UP:
                            self.next_direction1 = Direction.DOWN
                        elif event.key in (pygame.K_a) and self.snake_direction1 != Direction.RIGHT:
                            self.next_direction1 = Direction.LEFT
                        elif event.key in (pygame.K_d) and self.snake_direction1 != Direction.LEFT:
                            self.next_direction1 = Direction.RIGHT
                        # Spieler 2 steuert mit Pfeiltasten
                        if event.key == pygame.K_UP and self.snake_direction2 != Direction.DOWN:
                            self.next_direction2 = Direction.UP
                        elif event.key == pygame.K_DOWN and self.snake_direction2 != Direction.UP:
                            self.next_direction2 = Direction.DOWN
                        elif event.key == pygame.K_LEFT and self.snake_direction2 != Direction.RIGHT:
                            self.next_direction2 = Direction.LEFT
                        elif event.key == pygame.K_RIGHT and self.snake_direction2 != Direction.LEFT:
                            self.next_direction2 = Direction.RIGHT
                elif self.game_state == GameState.PAUSE:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.set_state(GameState.GAME)
                elif self.game_state == GameState.GAME_OVER and self.leaderboard_mode:
                    if event.key == pygame.K_RETURN:
                        if self.name_input.strip():
                            self.leaderboard.append((self.name_input.strip(), self.score))
                            self.leaderboard.sort(key=lambda x: x[1], reverse=True)
                            self.leaderboard = self.leaderboard[:10]
                            with open(LEADERBOARD_FILE, "w") as f:
                                for entry in self.leaderboard:
                                    f.write(f"{entry[0]},{entry[1]}\n")
                            self.set_state(GameState.INTRO)
                    elif event.key == pygame.K_BACKSPACE:
                        self.name_input = self.name_input[:-1]
                    elif event.unicode.isalnum() or event.unicode.isspace():
                        if len(self.name_input) < 15:
                            self.name_input += event.unicode
                elif self.game_state == GameState.SETTINGS and event.key == pygame.K_ESCAPE:
                    self.set_state(GameState.INTRO)
                elif self.game_state == GameState.CONTROLS and event.key == pygame.K_ESCAPE:
                    self.set_state(GameState.INTRO)
                elif event.key == pygame.K_f:
                    self.settings['fullscreen'] = not self.settings['fullscreen']
                    if self.settings['fullscreen']:
                        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            if self.game_state == GameState.INTRO:
                for btn in self.intro_buttons:
                    btn.check_hover(mouse_pos)
                    btn.handle_event(event)
            elif self.game_state == GameState.PAUSE:
                for btn in self.pause_buttons:
                    btn.check_hover(mouse_pos)
                    btn.handle_event(event)
            elif self.game_state == GameState.GAME_OVER:
                for btn in self.game_over_buttons:
                    btn.check_hover(mouse_pos)
                    btn.handle_event(event)
            elif self.game_state in (GameState.SETTINGS, GameState.CONTROLS):
                for elem in self.settings_elements:
                    elem.check_hover(mouse_pos)
                    elem.handle_event(event)
            elif self.game_state == GameState.CUSTOMIZATION:
                self.custom_menu.handle_event(event)

    def update(self):
        current_time = time.time()
        # Auto-Shoot im Einzelspieler- bzw. im 2-Spieler-Modus (immer aktiv)
        self.auto_shoot()
        # Normale Gegner spawnen (selten)
        if random.random() < 0.002:
            self.enemies.append(NormalEnemy())
        for enemy in self.enemies:
            enemy.update()
        # Kollision: Spielerprojektile treffen Gegner
        for enemy in self.enemies[:]:
            enemy_rect = enemy.get_rect()
            for proj in self.projectiles:
                proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if enemy_rect.colliderect(proj_rect):
                    enemy.health -= 1
                    if enemy.health <= 0:
                        try:
                            self.enemies.remove(enemy)
                        except ValueError:
                            pass
                        self.score += 20
                        self.add_achievement("Nice One! Enemy Down!")
                    if SOUNDS.get("gegner"):
                        SOUNDS["gegner"].play()
        # Kollision: Spieler berühren Gegner (Schaden)
        if self.player_count == 1 and self.snake:
            head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            for enemy in self.enemies:
                if head_rect.colliderect(enemy.get_rect()):
                    if SOUNDS.get("damage"):
                        SOUNDS["damage"].play()
                    self.handle_death()
        elif self.player_count == 2:
            for snake in [self.snake1, self.snake2]:
                if snake:
                    head_rect = pygame.Rect(snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    for enemy in self.enemies:
                        if head_rect.colliderect(enemy.get_rect()):
                            if SOUNDS.get("damage"):
                                SOUNDS["damage"].play()
                            self.handle_death()
        # Boss-Projektile treffen Spieler
    def update_projectiles(self):
        current_time = time.time()
        new_proj = []
        for proj in self.projectiles:
            dx, dy = proj['dir']
            new_x = proj['pos'][0] + dx
            new_y = proj['pos'][1] + dy
            proj['pos'] = (new_x, new_y)
            # Falls es sich um ein Boss-Projektil handelt, nicht mit dem Boss kollidieren lassen
            if not proj.get("from_boss", False):
                if self.boss and self.boss.get_rect().colliderect(pygame.Rect(new_x * GRID_SIZE, new_y * GRID_SIZE, GRID_SIZE, GRID_SIZE)):
                    self.boss.health -= 10
                    if self.boss.health <= 0:
                        self.boss = None
                        self.game_state = GameState.GAME
                        self.boss_spawn_timer = current_time + 60 + random.randint(0,30)
                        self.score += 100 * self.level
                        self.add_achievement("Boss besiegt! Boss Down Easy Going !!")
                        self.effects['boss_loot'] = current_time + 10
                    continue
            # Normale Kollisionsprüfung für Spielerprojektile
            size = GRID_SIZE
            if proj.get("from_boss", False):
                scale_factor = proj.get("scale", 2)
                size = int(GRID_SIZE * scale_factor)
            if new_x < 0 or new_x >= GRID_WIDTH or new_y < 0 or new_y >= GRID_HEIGHT:
                continue
            proj_rect = pygame.Rect(new_x * GRID_SIZE, new_y * GRID_SIZE, size, size)
            target = self.snake1[0] if self.player_count == 2 and self.snake1 else (self.snake[0] if self.snake else None)
            if target:
                head_rect = pygame.Rect(target[0] * GRID_SIZE, target[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if head_rect.colliderect(proj_rect):
                    # Eigene Projektile (nicht von Bossen) verursachen keinen Schaden an sich selbst
                    if not proj.get("from_boss", False):
                        continue
            new_proj.append(proj)
        self.projectiles = new_proj

        # Bonus-Loot-Effekt
        if self.effects.get('boss_loot', 0) > current_time:
            if random.random() < 0.01:
                self.spawn_new_item()
        # Portal-Management
        if self.portal:
            if current_time > self.portal.start_time + self.portal.duration:
                self.portal = None
        else:
            if current_time > self.portal_spawn_cooldown and random.random() < 0.005:
                self.portal = Portal()
        if self.portal_effect_active and current_time > self.portal_effect_end:
            self.portal_effect_active = False
            self.background.fill((102, 51, 0))
            for i in range(0, WINDOW_WIDTH, GRID_SIZE * 2):
                for j in range(0, WINDOW_HEIGHT, GRID_SIZE * 2):
                    pygame.draw.rect(self.background, (153, 102, 51), (i, j, GRID_SIZE, GRID_SIZE))
            self.intro_bg = self.menu_bg.copy()
        if self.game_state == GameState.GAME and current_time >= self.boss_spawn_timer and self.boss is None:
            self.start_boss_fight()
        for eff in list(self.effects.keys()):
            if self.effects[eff] > 0 and current_time > self.effects[eff]:
                self.effects[eff] = 0
                if eff == 'speed_boost':
                    self.speed = max(self.settings['initial_speed'], self.speed - 3)
                elif eff == 'speed_reduction':
                    self.speed = min(MAX_SPEED, self.speed + 3)
        snake_update_rate = 1.0 / self.speed
        delta = current_time - self.last_update_time
        if delta >= snake_update_rate:
            self.last_update_time = current_time
            if self.player_count == 2:
                if self.portal and self.snake1 and (self.snake1[0][0] == self.portal.x and self.snake1[0][1] == self.portal.y):
                    self.activate_portal(self.portal.event)
                    self.portal_effect_active = True
                    self.portal = None
            else:
                if self.portal and self.snake and (self.snake[0][0] == self.portal.x and self.snake[0][1] == self.portal.y):
                    self.activate_portal(self.portal.event)
                    self.portal_effect_active = True
                    self.portal = None
            if self.player_count == 2:
                if self.snake1:
                    head1 = self.snake1[0]
                    self.snake_direction1 = self.next_direction1 if hasattr(self, 'next_direction1') else Direction.RIGHT
                    new_head1 = (head1[0] + self.snake_direction1.value[0], head1[1] + self.snake_direction1.value[1])
                    if new_head1[0] < 0 or new_head1[0] >= GRID_WIDTH or new_head1[1] < 0 or new_head1[1] >= GRID_HEIGHT:
                        if self.effects['invincibility'] <= current_time:
                            self.handle_death()
                            return
                        else:
                            new_head1 = (new_head1[0] % GRID_WIDTH, new_head1[1] % GRID_HEIGHT)
                    if new_head1 in self.snake1[1:]:
                        if self.effects['invincibility'] <= current_time:
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
                    new_head2 = (head2[0] + self.snake_direction2.value[0], head2[1] + self.snake_direction2.value[1])
                    if new_head2[0] < 0 or new_head2[0] >= GRID_WIDTH or new_head2[1] < 0 or new_head2[1] >= GRID_HEIGHT:
                        if self.effects['invincibility'] <= current_time:
                            self.handle_death()
                            return
                        else:
                            new_head2 = (new_head2[0] % GRID_WIDTH, new_head2[1] % GRID_HEIGHT)
                    if new_head2 in self.snake2[1:]:
                        if self.effects['invincibility'] <= current_time:
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
                if self.snake:
                    head = self.snake[0]
                    self.snake_direction = self.next_direction if hasattr(self, 'next_direction') else Direction.RIGHT
                    new_head = (head[0] + self.snake_direction.value[0], head[1] + self.snake_direction.value[1])
                    if new_head[0] < 0 or new_head[0] >= GRID_WIDTH or new_head[1] < 0 or new_head[1] >= GRID_HEIGHT:
                        if self.effects['invincibility'] <= 0:
                            self.handle_death()
                            return
                        else:
                            new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
                    if new_head in self.snake[:-1]:
                        if self.effects['invincibility'] <= 0:
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
                target = self.snake[0] if self.player_count == 1 and self.snake else (self.snake1[0] if self.player_count == 2 and self.snake1 else None)
                if target and self.check_boss_collision(target):
                    if SOUNDS.get("damage"):
                        SOUNDS["damage"].play()
                    self.handle_death()
                else:
                    act = self.boss.update(current_time)
                    if act == "aoe":
                        boss_rect = self.boss.get_rect()
                        target = self.snake[0] if self.player_count == 1 and self.snake else (self.snake1[0] if self.player_count == 2 and self.snake1 else None)
                        if target:
                            head_pixel = (target[0] * GRID_SIZE + GRID_SIZE//2, target[1] * GRID_SIZE + GRID_SIZE//2)
                            if boss_rect.inflate(40,40).collidepoint(head_pixel):
                                if SOUNDS.get("damage"):
                                    SOUNDS["damage"].play()
                                self.handle_death()
                    elif act == "boss_shoot":
                        target = self.snake[0] if self.player_count == 1 and self.snake else (self.snake1[0] if self.player_count == 2 and self.snake1 else None)
                        if target:
                            dx = 1 if target[0] > self.boss.x else -1 if target[0] < self.boss.x else 0
                            dy = 1 if target[1] > self.boss.y else -1 if target[1] < self.boss.y else 0
                            proj_effect = "damage"
                            boss_proj_img = random.choice(BOSS_PROJECTILES) if BOSS_PROJECTILES else PROJECTILE_IMG
                            proj = {'pos': (self.boss.x, self.boss.y),
                                    'dir': (dx, dy),
                                    "effect": proj_effect,
                                    "from_boss": True,
                                    "image": boss_proj_img}
                            self.projectiles.append(proj)
            if random.random() < 0.005 * self.settings['difficulty'] and len(self.items) < 5:
                self.spawn_new_item()
            self.update_projectiles()
        # Boss-Projektile treffen Spieler
        for proj in self.projectiles:
            if proj.get("from_boss", False):
                if self.player_count == 1 and self.snake:
                    head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if head_rect.colliderect(proj_rect):
                        if SOUNDS.get("damage"):
                            SOUNDS["damage"].play()
                        self.handle_death()
                elif self.player_count == 2:
                    for snake in [self.snake1, self.snake2]:
                        if snake:
                            head_rect = pygame.Rect(snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            if head_rect.colliderect(proj_rect):
                                if SOUNDS.get("damage"):
                                    SOUNDS["damage"].play()
                                self.handle_death()

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
        elif item.type == ItemType.PROJECTILE_SHOOT:
            # Multi-Shoot-Effekt: 30 Sekunden lang erhält der Spieler zusätzliche Auto-Shoot-Projektile
            self.effects['projectile_shoot'] = current_time + 30
            self.extra_auto_shots = min(6, self.extra_auto_shots + 1)
            self.score += 40
            self.experience += 20
            self.add_achievement("Multi-Shoot aktiviert!")
        if self.experience >= self.exp_to_next_level:
            self.level_up()

    def handle_death(self):
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
                self.snake1 = [(GRID_WIDTH//2, GRID_HEIGHT//2)]
                self.snake2 = [(GRID_WIDTH//2, GRID_HEIGHT//2 + 2)]
                self.snake_direction1 = Direction.RIGHT
                self.snake_direction2 = Direction.RIGHT
                self.next_direction1 = Direction.RIGHT
                self.next_direction2 = Direction.RIGHT
            else:
                self.snake = [(GRID_WIDTH//2, GRID_HEIGHT//2)]
                self.snake_direction = Direction.RIGHT
                self.next_direction = Direction.RIGHT
            self.effects['invincibility'] = time.time() + 3

    def draw(self):
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
            self.draw_settings()
        elif self.game_state == GameState.LEADERBOARD:
            self.draw_leaderboard()
        # Boss-Spawn-Cooldown-Anzeige (nur im Spiel)
        if self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
            if self.boss_spawn_timer > time.time():
                cooldown = int(self.boss_spawn_timer - time.time())
                cd_txt = pygame.font.SysFont('Arial', 16, bold=True).render(f"Boss spawn in: {cooldown}s", True, ORANGE)
                self.screen.blit(cd_txt, (10, WINDOW_HEIGHT - 30))
        pygame.draw.rect(self.screen, DARK_GREY, (10, 5, 240, 40), 3)
        pygame.display.update()

    def draw_intro(self):
        self.screen.blit(self.menu_bg, (0, 0))
        if TITLE_IMG:
            scaled_title = pygame.transform.scale(TITLE_IMG, (TITLE_IMG.get_width()*2, TITLE_IMG.get_height()*2))
            self.screen.blit(scaled_title, (WINDOW_WIDTH//2 - scaled_title.get_width()//2, 20))
        title_txt = pygame.font.SysFont('Comic Sans MS', 60, bold=True).render("Dark-Snake", True, (50,50,50))
        self.screen.blit(title_txt, (WINDOW_WIDTH//2 - title_txt.get_width()//2, 100))
        for btn in self.intro_buttons:
            btn.draw(self.screen)

    def draw_game(self):
        self.screen.blit(self.background, (0, 0))
        if self.portal:
            self.portal.draw(self.screen)
        for item in self.items:
            item.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        if self.player_count == 2:
            # Spieler 1 (WASD): Kopf rotiert entsprechend
            for i, seg in enumerate(self.snake1):
                x = seg[0] * GRID_SIZE
                y = seg[1] * GRID_SIZE
                if i == 0:
                    rotated = pygame.transform.rotate(SNAKE_HEAD_IMG, -self.snake_direction1.value[0]*90)
                    self.screen.blit(rotated, (x, y))
                else:
                    self.screen.blit(SNAKE_BODY_IMG, (x, y))
            # Spieler 2 (Pfeiltasten): Kopf rotiert entsprechend
            for i, seg in enumerate(self.snake2):
                x = seg[0] * GRID_SIZE
                y = seg[1] * GRID_SIZE
                if i == 0:
                    rotated = pygame.transform.rotate(SNAKE_HEAD_BETA, -self.snake_direction2.value[0]*90)
                    self.screen.blit(rotated, (x, y))
                else:
                    self.screen.blit(SNAKE_BODY_BETA, (x, y))
        else:
            for i, seg in enumerate(self.snake):
                x = seg[0] * GRID_SIZE
                y = seg[1] * GRID_SIZE
                if i == 0:
                    head_img = self.settings['custom_head'] if self.settings['custom_head'] is not None else SNAKE_HEAD_IMG
                    rotated = pygame.transform.rotate(head_img, -self.snake_direction.value[0]*90)
                    self.screen.blit(rotated, (x, y))
                else:
                    self.screen.blit(SNAKE_BODY_IMG, (x, y))
        if self.boss:
            self.boss.draw(self.screen)
        for proj in self.projectiles:
            proj_x = int(proj['pos'][0] * GRID_SIZE)
            proj_y = int(proj['pos'][1] * GRID_SIZE)
            if proj.get("from_boss", False):
                proj_img = pygame.transform.scale(proj.get("image", PROJECTILE_IMG), (GRID_SIZE*2, GRID_SIZE*2))
            else:
                proj_img = pygame.transform.scale(PROJECTILE_IMG, (GRID_SIZE, GRID_SIZE))
            self.screen.blit(proj_img, (proj_x, proj_y))
        self.draw_hud()
        if self.dice_result is not None and time.time() <= self.dice_display_until:
            self.draw_dice_result()

    def draw_hud(self):
        score_txt = pygame.font.SysFont('Arial', 30).render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_txt, (20, 10))
        for i in range(self.lives):
            pygame.draw.rect(self.screen, RED, (WINDOW_WIDTH - 35 - i * 30, 15, 20, 20))
        level_txt = pygame.font.SysFont('Arial', 20).render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_txt, (20, 45))
        exp_width = 200
        exp_height = 10
        pygame.draw.rect(self.screen, DARK_GREY, (20, 70, exp_width, exp_height))
        perc = min(1.0, self.experience / self.exp_to_next_level)
        pygame.draw.rect(self.screen, GREEN, (20, 70, int(exp_width * perc), exp_height))
        y_eff = 90
        for eff, end in self.effects.items():
            if end > 0:
                t_left = max(0, end - time.time())
                eff_txt = pygame.font.SysFont('Arial', 20, bold=True).render(f"{eff.replace('_', ' ').title()}: {t_left:.1f}s", True, ORANGE)
                txt_rect = eff_txt.get_rect(topleft=(20, y_eff))
                s = pygame.Surface((txt_rect.width, txt_rect.height), pygame.SRCALPHA)
                s.fill((0, 0, 0, 204))
                self.screen.blit(s, (20, y_eff))
                self.screen.blit(eff_txt, (20, y_eff))
                y_eff += 22
        y_ach = 130
        for msg, expire in self.achievement_messages[:]:
            if time.time() > expire:
                self.achievement_messages.remove((msg, expire))
                continue
            ach_txt = pygame.font.SysFont('Arial', 20, bold=True).render(msg, True, ORANGE)
            self.screen.blit(ach_txt, (20, y_ach))
            y_ach += 22

    def draw_dice_result(self):
        dice_rect = pygame.Rect(WINDOW_WIDTH//2 - 50, WINDOW_HEIGHT//2 - 50, 100, 100)
        pygame.draw.rect(self.screen, PURPLE, dice_rect, border_radius=15)
        pygame.draw.rect(self.screen, WHITE, dice_rect, 2, border_radius=15)
        res_txt = pygame.font.SysFont('Arial', 50).render(str(self.dice_result), True, WHITE)
        self.screen.blit(res_txt, (WINDOW_WIDTH//2 - res_txt.get_width()//2, WINDOW_HEIGHT//2 - res_txt.get_height()//2))
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
        self.screen.blit(desc, (WINDOW_WIDTH//2 - desc.get_width()//2, WINDOW_HEIGHT//2 + 40))

    def draw_pause(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        pause_txt = pygame.font.SysFont('Arial', 50).render("PAUSE", True, WHITE)
        self.screen.blit(pause_txt, (WINDOW_WIDTH//2 - pause_txt.get_width()//2, 100))
        for btn in self.pause_buttons:
            btn.draw(self.screen)

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        go_txt = pygame.font.SysFont('Arial', 50).render("GAME OVER", True, RED)
        self.screen.blit(go_txt, (WINDOW_WIDTH//2 - go_txt.get_width()//2, 100))
        score_txt = pygame.font.SysFont('Arial', 30).render(f"Dein Score: {self.score}", True, WHITE)
        self.screen.blit(score_txt, (WINDOW_WIDTH//2 - score_txt.get_width()//2, 180))
        if self.leaderboard_mode:
            in_txt = pygame.font.SysFont('Arial', 30).render("Gib deinen Namen ein:", True, WHITE)
            self.screen.blit(in_txt, (WINDOW_WIDTH//2 - in_txt.get_width()//2, 230))
            input_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, 270, 300, 40)
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

    def draw_settings(self):
        self.screen.fill(DARK_GREY)
        title_txt = pygame.font.SysFont('Arial', 50).render("EINSTELLUNGEN", True, WHITE)
        self.screen.blit(title_txt, (WINDOW_WIDTH//2 - title_txt.get_width()//2, 50))
        for elem in self.settings_elements:
            elem.draw(self.screen)
        pygame.display.update()

    def draw_leaderboard(self):
        self.screen.fill(DARK_GREY)
        title_txt = pygame.font.SysFont('Arial', 50).render("BESTENLISTE", True, GOLDEN)
        self.screen.blit(title_txt, (WINDOW_WIDTH//2 - title_txt.get_width()//2, 50))
        y_pos = 150
        if not self.leaderboard:
            none_txt = pygame.font.SysFont('Arial', 30).render("Keine Einträge vorhanden", True, WHITE)
            self.screen.blit(none_txt, (WINDOW_WIDTH//2 - none_txt.get_width()//2, y_pos))
        else:
            for i, (name, score) in enumerate(self.leaderboard[:10]):
                col = GOLDEN if i == 0 else ((192, 192, 192) if i == 1 else (205, 127, 50) if i == 2 else WHITE)
                entry_txt = pygame.font.SysFont('Arial', 30).render(f"{i+1}. {name}: {score}", True, col)
                self.screen.blit(entry_txt, (WINDOW_WIDTH//2 - 150, y_pos))
                y_pos += 40
        back_btn = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 80, 200, 60, "ZURÜCK", color=PURPLE, action=lambda: self.confirm_back_to_main())
        back_btn.draw(self.screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mpos = pygame.mouse.get_pos()
                if back_btn.check_hover(mpos):
                    back_btn.handle_event(event)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.set_state(GameState.INTRO)
                    
    def auto_shoot(self):
        current_time = time.time()
        if current_time - self.last_auto_shoot >= 3:
            self.last_auto_shoot = current_time
            head = None
            if self.player_count == 1 and self.snake:
                head = self.snake[0]
            elif self.player_count == 2 and self.snake1:
                head = self.snake1[0]
            if head is None:
                return
            target = None
            min_dist = float("inf")
            if self.enemies:
                for enemy in self.enemies:
                    dist = sqrt((head[0] - enemy.x) ** 2 + (head[1] - enemy.y) ** 2)
                    if dist < min_dist:
                        min_dist = dist
                        target = enemy
            if target:
                dx = target.x - head[0]
                dy = target.y - head[1]
                angle = atan2(dy, dx)
                dir_x = cos(angle) * 2
                dir_y = sin(angle) * 2
            else:
                if self.player_count == 1:
                    dir_x, dir_y = self.snake_direction.value[0] * 2, self.snake_direction.value[1] * 2
                else:
                    dir_x, dir_y = self.snake_direction1.value[0] * 2, self.snake_direction1.value[1] * 2
            proj = {'pos': (head[0], head[1]),
                    'dir': (dir_x, dir_y),
                    "effect": "damage"}
            self.projectiles.append(proj)
            for _ in range(self.extra_auto_shots):
                deviation = random.uniform(-0.3, 0.3)
                proj_extra = {'pos': (head[0], head[1]),
                              'dir': (dir_x + deviation, dir_y + deviation),
                              "effect": "damage"}
                self.projectiles.append(proj_extra)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button != 1:
                continue
            elif event.type == pygame.KEYDOWN:
                if self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.set_state(GameState.PAUSE)
                    # Einzelspieler: Steuerung mit WASD und Pfeiltasten
                    if self.player_count == 1:
                        if event.key in (pygame.K_UP, pygame.K_w) and self.snake_direction != Direction.DOWN:
                            self.next_direction = Direction.UP
                        elif event.key in (pygame.K_DOWN, pygame.K_s) and self.snake_direction != Direction.UP:
                            self.next_direction = Direction.DOWN
                        elif event.key in (pygame.K_LEFT, pygame.K_a) and self.snake_direction != Direction.RIGHT:
                            self.next_direction = Direction.LEFT
                        elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.snake_direction != Direction.LEFT:
                            self.next_direction = Direction.RIGHT
                    # Zweispielermodus:
                    elif self.player_count == 2:
                        # Spieler 1 (WASD)
                        if event.key == pygame.K_w and self.snake_direction1 != Direction.DOWN:
                            self.next_direction1 = Direction.UP
                        elif event.key == pygame.K_s and self.snake_direction1 != Direction.UP:
                            self.next_direction1 = Direction.DOWN
                        elif event.key == pygame.K_a and self.snake_direction1 != Direction.RIGHT:
                            self.next_direction1 = Direction.LEFT
                        elif event.key == pygame.K_d and self.snake_direction1 != Direction.LEFT:
                            self.next_direction1 = Direction.RIGHT
                        # Spieler 2 (Pfeiltasten)
                        if event.key == pygame.K_UP and self.snake_direction2 != Direction.DOWN:
                            self.next_direction2 = Direction.UP
                        elif event.key == pygame.K_DOWN and self.snake_direction2 != Direction.UP:
                            self.next_direction2 = Direction.DOWN
                        elif event.key == pygame.K_LEFT and self.snake_direction2 != Direction.RIGHT:
                            self.next_direction2 = Direction.LEFT
                        elif event.key == pygame.K_RIGHT and self.snake_direction2 != Direction.LEFT:
                            self.next_direction2 = Direction.RIGHT
                elif self.game_state == GameState.PAUSE:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        self.set_state(GameState.GAME)
                elif self.game_state == GameState.GAME_OVER and self.leaderboard_mode:
                    if event.key == pygame.K_RETURN:
                        if self.name_input.strip():
                            self.leaderboard.append((self.name_input.strip(), self.score))
                            self.leaderboard.sort(key=lambda x: x[1], reverse=True)
                            self.leaderboard = self.leaderboard[:10]
                            with open(LEADERBOARD_FILE, "w") as f:
                                for entry in self.leaderboard:
                                    f.write(f"{entry[0]},{entry[1]}\n")
                            self.set_state(GameState.INTRO)
                    elif event.key == pygame.K_BACKSPACE:
                        self.name_input = self.name_input[:-1]
                    elif event.unicode.isalnum() or event.unicode.isspace():
                        if len(self.name_input) < 15:
                            self.name_input += event.unicode
                elif self.game_state == GameState.SETTINGS and event.key == pygame.K_ESCAPE:
                    self.set_state(GameState.INTRO)
                elif self.game_state == GameState.CONTROLS and event.key == pygame.K_ESCAPE:
                    self.set_state(GameState.INTRO)
                elif event.key == pygame.K_f:
                    self.settings['fullscreen'] = not self.settings['fullscreen']
                    if self.settings['fullscreen']:
                        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            if self.game_state == GameState.INTRO:
                for btn in self.intro_buttons:
                    btn.check_hover(mouse_pos)
                    btn.handle_event(event)
            elif self.game_state == GameState.PAUSE:
                for btn in self.pause_buttons:
                    btn.check_hover(mouse_pos)
                    btn.handle_event(event)
            elif self.game_state == GameState.GAME_OVER:
                for btn in self.game_over_buttons:
                    btn.check_hover(mouse_pos)
                    btn.handle_event(event)
            elif self.game_state in (GameState.SETTINGS, GameState.CONTROLS):
                for elem in self.settings_elements:
                    elem.check_hover(mouse_pos)
                    elem.handle_event(event)
            elif self.game_state == GameState.CUSTOMIZATION:
                self.custom_menu.handle_event(event)

    def update(self):
        current_time = time.time()
        self.auto_shoot()
        if random.random() < 0.002:
            self.enemies.append(NormalEnemy())
        for enemy in self.enemies:
            enemy.update()
        for enemy in self.enemies[:]:
            enemy_rect = enemy.get_rect()
            for proj in self.projectiles:
                proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if enemy_rect.colliderect(proj_rect):
                    enemy.health -= 1
                    if enemy.health <= 0:
                        try:
                            self.enemies.remove(enemy)
                        except ValueError:
                            pass
                        self.score += 20
                        self.add_achievement("Nice One! Enemy Down!")
                    if SOUNDS.get("gegner"):
                        SOUNDS["gegner"].play()
        if self.player_count == 1 and self.snake:
            head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            for enemy in self.enemies:
                if head_rect.colliderect(enemy.get_rect()):
                    if SOUNDS.get("damage"):
                        SOUNDS["damage"].play()
                    self.handle_death()
        elif self.player_count == 2:
            for snake in [self.snake1, self.snake2]:
                if snake:
                    head_rect = pygame.Rect(snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    for enemy in self.enemies:
                        if head_rect.colliderect(enemy.get_rect()):
                            if SOUNDS.get("damage"):
                                SOUNDS["damage"].play()
                            self.handle_death()
        for proj in self.projectiles:
            if proj.get("from_boss", False):
                if self.player_count == 1 and self.snake:
                    head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if head_rect.colliderect(proj_rect):
                        if SOUNDS.get("damage"):
                            SOUNDS["damage"].play()
                        self.handle_death()
                elif self.player_count == 2:
                    for snake in [self.snake1, self.snake2]:
                        if snake:
                            head_rect = pygame.Rect(snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            if head_rect.colliderect(proj_rect):
                                if SOUNDS.get("damage"):
                                    SOUNDS["damage"].play()
                                self.handle_death()
        if self.effects.get('boss_loot', 0) > current_time:
            if random.random() < 0.01:
                self.spawn_new_item()
        if self.portal:
            if current_time > self.portal.start_time + self.portal.duration:
                self.portal = None
        else:
            if current_time > self.portal_spawn_cooldown and random.random() < 0.005:
                self.portal = Portal()
        if self.portal_effect_active and current_time > self.portal_effect_end:
            self.portal_effect_active = False
            self.background.fill((102, 51, 0))
            for i in range(0, WINDOW_WIDTH, GRID_SIZE * 2):
                for j in range(0, WINDOW_HEIGHT, GRID_SIZE * 2):
                    pygame.draw.rect(self.background, (153, 102, 51), (i, j, GRID_SIZE, GRID_SIZE))
            self.intro_bg = self.menu_bg.copy()
        if self.game_state == GameState.GAME and current_time >= self.boss_spawn_timer and self.boss is None:
            self.start_boss_fight()
        for eff in list(self.effects.keys()):
            if self.effects[eff] > 0 and current_time > self.effects[eff]:
                self.effects[eff] = 0
                if eff == 'speed_boost':
                    self.speed = max(self.settings['initial_speed'], self.speed - 3)
                elif eff == 'speed_reduction':
                    self.speed = min(MAX_SPEED, self.speed + 3)
        snake_update_rate = 1.0 / self.speed
        delta = current_time - self.last_update_time
        if delta >= snake_update_rate:
            self.last_update_time = current_time
            if self.player_count == 2:
                if self.portal and self.snake1 and (self.snake1[0][0] == self.portal.x and self.snake1[0][1] == self.portal.y):
                    self.activate_portal(self.portal.event)
                    self.portal_effect_active = True
                    self.portal = None
            else:
                if self.portal and self.snake and (self.snake[0][0] == self.portal.x and self.snake[0][1] == self.portal.y):
                    self.activate_portal(self.portal.event)
                    self.portal_effect_active = True
                    self.portal = None
            if self.player_count == 2:
                if self.snake1:
                    head1 = self.snake1[0]
                    self.snake_direction1 = self.next_direction1 if hasattr(self, 'next_direction1') else Direction.RIGHT
                    new_head1 = (head1[0] + self.snake_direction1.value[0], head1[1] + self.snake_direction1.value[1])
                    if new_head1[0] < 0 or new_head1[0] >= GRID_WIDTH or new_head1[1] < 0 or new_head1[1] >= GRID_HEIGHT:
                        if self.effects['invincibility'] <= current_time:
                            self.handle_death()
                            return
                        else:
                            new_head1 = (new_head1[0] % GRID_WIDTH, new_head1[1] % GRID_HEIGHT)
                    if new_head1 in self.snake1[1:]:
                        if self.effects['invincibility'] <= current_time:
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
                    new_head2 = (head2[0] + self.snake_direction2.value[0], head2[1] + self.snake_direction2.value[1])
                    if new_head2[0] < 0 or new_head2[0] >= GRID_WIDTH or new_head2[1] < 0 or new_head2[1] >= GRID_HEIGHT:
                        if self.effects['invincibility'] <= current_time:
                            self.handle_death()
                            return
                        else:
                            new_head2 = (new_head2[0] % GRID_WIDTH, new_head2[1] % GRID_HEIGHT)
                    if new_head2 in self.snake2[1:]:
                        if self.effects['invincibility'] <= current_time:
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
                if self.snake:
                    head = self.snake[0]
                    self.snake_direction = self.next_direction if hasattr(self, 'next_direction') else Direction.RIGHT
                    new_head = (head[0] + self.snake_direction.value[0], head[1] + self.snake_direction.value[1])
                    if new_head[0] < 0 or new_head[0] >= GRID_WIDTH or new_head[1] < 0 or new_head[1] >= GRID_HEIGHT:
                        if self.effects['invincibility'] <= 0:
                            self.handle_death()
                            return
                        else:
                            new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
                    if new_head in self.snake[:-1]:
                        if self.effects['invincibility'] <= 0:
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
                target = self.snake[0] if self.player_count == 1 and self.snake else (self.snake1[0] if self.player_count == 2 and self.snake1 else None)
                if target and self.check_boss_collision(target):
                    if SOUNDS.get("damage"):
                        SOUNDS["damage"].play()
                    self.handle_death()
                else:
                    act = self.boss.update(current_time)
                    if act == "aoe":
                        boss_rect = self.boss.get_rect()
                        target = self.snake[0] if self.player_count == 1 and self.snake else (self.snake1[0] if self.player_count == 2 and self.snake1 else None)
                        if target:
                            head_pixel = (target[0] * GRID_SIZE + GRID_SIZE//2, target[1] * GRID_SIZE + GRID_SIZE//2)
                            if boss_rect.inflate(40,40).collidepoint(head_pixel):
                                if SOUNDS.get("damage"):
                                    SOUNDS["damage"].play()
                                self.handle_death()
                    elif act == "boss_shoot":
                        target = self.snake[0] if self.player_count == 1 and self.snake else (self.snake1[0] if self.player_count == 2 and self.snake1 else None)
                        if target:
                            dx = 1 if target[0] > self.boss.x else -1 if target[0] < self.boss.x else 0
                            dy = 1 if target[1] > self.boss.y else -1 if target[1] < self.boss.y else 0
                            proj_effect = "damage"
                            boss_proj_img = random.choice(BOSS_PROJECTILES) if BOSS_PROJECTILES else PROJECTILE_IMG
                            proj = {'pos': (self.boss.x, self.boss.y),
                                    'dir': (dx, dy),
                                    "effect": proj_effect,
                                    "from_boss": True,
                                    "image": boss_proj_img}
                            self.projectiles.append(proj)
            if random.random() < 0.005 * self.settings['difficulty'] and len(self.items) < 5:
                self.spawn_new_item()
            self.update_projectiles()
        for proj in self.projectiles:
            if proj.get("from_boss", False):
                if self.player_count == 1 and self.snake:
                    head_rect = pygame.Rect(self.snake[0][0] * GRID_SIZE, self.snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                    if head_rect.colliderect(proj_rect):
                        if SOUNDS.get("damage"):
                            SOUNDS["damage"].play()
                        self.handle_death()
                elif self.player_count == 2:
                    for snake in [self.snake1, self.snake2]:
                        if snake:
                            head_rect = pygame.Rect(snake[0][0] * GRID_SIZE, snake[0][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            proj_rect = pygame.Rect(proj['pos'][0] * GRID_SIZE, proj['pos'][1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                            if head_rect.colliderect(proj_rect):
                                if SOUNDS.get("damage"):
                                    SOUNDS["damage"].play()
                                self.handle_death()

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
        elif item.type == ItemType.PROJECTILE_SHOOT:
            self.effects['projectile_shoot'] = current_time + 30
            self.extra_auto_shots = min(6, self.extra_auto_shots + 1)
            self.score += 40
            self.experience += 20
            self.add_achievement("Multi-Shoot aktiviert!")
        if self.experience >= self.exp_to_next_level:
            self.level_up()

    def handle_death(self):
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
                self.snake1 = [(GRID_WIDTH//2, GRID_HEIGHT//2)]
                self.snake2 = [(GRID_WIDTH//2, GRID_HEIGHT//2 + 2)]
                self.snake_direction1 = Direction.RIGHT
                self.snake_direction2 = Direction.RIGHT
                self.next_direction1 = Direction.RIGHT
                self.next_direction2 = Direction.RIGHT
            else:
                self.snake = [(GRID_WIDTH//2, GRID_HEIGHT//2)]
                self.snake_direction = Direction.RIGHT
                self.next_direction = Direction.RIGHT
            self.effects['invincibility'] = time.time() + 3

    def draw(self):
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
            self.draw_settings()
        elif self.game_state == GameState.LEADERBOARD:
            self.draw_leaderboard()
        if self.game_state in (GameState.GAME, GameState.BOSS_FIGHT):
            if self.boss_spawn_timer > time.time():
                cooldown = int(self.boss_spawn_timer - time.time())
                cd_txt = pygame.font.SysFont('Arial', 16, bold=True).render(f"Boss spawn in: {cooldown}s", True, ORANGE)
                self.screen.blit(cd_txt, (10, WINDOW_HEIGHT - 30))
        pygame.draw.rect(self.screen, DARK_GREY, (10, 5, 240, 40), 3)
        pygame.display.update()

    def draw_intro(self):
        self.screen.blit(self.menu_bg, (0, 0))
        if TITLE_IMG:
            scaled_title = pygame.transform.scale(TITLE_IMG, (TITLE_IMG.get_width()*2, TITLE_IMG.get_height()*2))
            self.screen.blit(scaled_title, (WINDOW_WIDTH//2 - scaled_title.get_width()//2, 20))
        title_txt = pygame.font.SysFont('Comic Sans MS', 60, bold=True).render("Dark-Snake", True, (50,50,50))
        self.screen.blit(title_txt, (WINDOW_WIDTH//2 - title_txt.get_width()//2, 100))
        for btn in self.intro_buttons:
            btn.draw(self.screen)

    def draw_game(self):
        self.screen.blit(self.background, (0, 0))
        if self.portal:
            self.portal.draw(self.screen)
        for item in self.items:
            item.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        if self.player_count == 2:
            for i, seg in enumerate(self.snake1):
                x = seg[0] * GRID_SIZE
                y = seg[1] * GRID_SIZE
                rotated = pygame.transform.rotate(SNAKE_HEAD_IMG, -self.snake_direction1.value[0]*90)
                self.screen.blit(rotated, (x, y))
            for i, seg in enumerate(self.snake2):
                x = seg[0] * GRID_SIZE
                y = seg[1] * GRID_SIZE
                rotated = pygame.transform.rotate(SNAKE_HEAD_BETA, -self.snake_direction2.value[0]*90)
                self.screen.blit(rotated, (x, y))
        else:
            for i, seg in enumerate(self.snake):
                x = seg[0] * GRID_SIZE
                y = seg[1] * GRID_SIZE
                if i == 0:
                    head_img = self.settings['custom_head'] if self.settings['custom_head'] is not None else SNAKE_HEAD_IMG
                    rotated = pygame.transform.rotate(head_img, -self.snake_direction.value[0]*90)
                    self.screen.blit(rotated, (x, y))
                else:
                    self.screen.blit(SNAKE_BODY_IMG, (x, y))
        if self.boss:
            self.boss.draw(self.screen)
        for proj in self.projectiles:
            proj_x = int(proj['pos'][0] * GRID_SIZE)
            proj_y = int(proj['pos'][1] * GRID_SIZE)
            if proj.get("from_boss", False):
                proj_img = pygame.transform.scale(proj.get("image", PROJECTILE_IMG), (GRID_SIZE*2, GRID_SIZE*2))
            else:
                proj_img = pygame.transform.scale(PROJECTILE_IMG, (GRID_SIZE, GRID_SIZE))
            self.screen.blit(proj_img, (proj_x, proj_y))
        self.draw_hud()
        if self.dice_result is not None and time.time() <= self.dice_display_until:
            self.draw_dice_result()

    def draw_hud(self):
        score_txt = pygame.font.SysFont('Arial', 30).render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_txt, (20, 10))
        for i in range(self.lives):
            pygame.draw.rect(self.screen, RED, (WINDOW_WIDTH - 35 - i * 30, 15, 20, 20))
        level_txt = pygame.font.SysFont('Arial', 20).render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_txt, (20, 45))
        exp_width = 200
        exp_height = 10
        pygame.draw.rect(self.screen, DARK_GREY, (20, 70, exp_width, exp_height))
        perc = min(1.0, self.experience / self.exp_to_next_level)
        pygame.draw.rect(self.screen, GREEN, (20, 70, int(exp_width * perc), exp_height))
        y_eff = 90
        for eff, end in self.effects.items():
            if end > 0:
                t_left = max(0, end - time.time())
                eff_txt = pygame.font.SysFont('Arial', 20, bold=True).render(f"{eff.replace('_', ' ').title()}: {t_left:.1f}s", True, ORANGE)
                txt_rect = eff_txt.get_rect(topleft=(20, y_eff))
                s = pygame.Surface((txt_rect.width, txt_rect.height), pygame.SRCALPHA)
                s.fill((0, 0, 0, 204))
                self.screen.blit(s, (20, y_eff))
                self.screen.blit(eff_txt, (20, y_eff))
                y_eff += 22
        y_ach = 130
        for msg, expire in self.achievement_messages[:]:
            if time.time() > expire:
                self.achievement_messages.remove((msg, expire))
                continue
            ach_txt = pygame.font.SysFont('Arial', 20, bold=True).render(msg, True, ORANGE)
            self.screen.blit(ach_txt, (20, y_ach))
            y_ach += 22

    def draw_dice_result(self):
        dice_rect = pygame.Rect(WINDOW_WIDTH//2 - 50, WINDOW_HEIGHT//2 - 50, 100, 100)
        pygame.draw.rect(self.screen, PURPLE, dice_rect, border_radius=15)
        pygame.draw.rect(self.screen, WHITE, dice_rect, 2, border_radius=15)
        res_txt = pygame.font.SysFont('Arial', 50).render(str(self.dice_result), True, WHITE)
        self.screen.blit(res_txt, (WINDOW_WIDTH//2 - res_txt.get_width()//2, WINDOW_HEIGHT//2 - res_txt.get_height()//2))
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
        self.screen.blit(desc, (WINDOW_WIDTH//2 - desc.get_width()//2, WINDOW_HEIGHT//2 + 40))

    def draw_pause(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        pause_txt = pygame.font.SysFont('Arial', 50).render("PAUSE", True, WHITE)
        self.screen.blit(pause_txt, (WINDOW_WIDTH//2 - pause_txt.get_width()//2, 100))
        for btn in self.pause_buttons:
            btn.draw(self.screen)

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        go_txt = pygame.font.SysFont('Arial', 50).render("GAME OVER", True, RED)
        self.screen.blit(go_txt, (WINDOW_WIDTH//2 - go_txt.get_width()//2, 100))
        score_txt = pygame.font.SysFont('Arial', 30).render(f"Dein Score: {self.score}", True, WHITE)
        self.screen.blit(score_txt, (WINDOW_WIDTH//2 - score_txt.get_width()//2, 180))
        if self.leaderboard_mode:
            in_txt = pygame.font.SysFont('Arial', 30).render("Highscore!! Dein Name?:", True, WHITE)
            self.screen.blit(in_txt, (WINDOW_WIDTH//2 - in_txt.get_width()//2, 230))
            input_rect = pygame.Rect(WINDOW_WIDTH//2 - 150, 270, 300, 40)
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

    def draw_settings(self):
        self.screen.fill(DARK_GREY)
        title_txt = pygame.font.SysFont('Arial', 50).render("EINSTELLUNGEN", True, WHITE)
        self.screen.blit(title_txt, (WINDOW_WIDTH//2 - title_txt.get_width()//2, 50))
        for elem in self.settings_elements:
            elem.draw(self.screen)
        pygame.display.update()
        

    def draw_leaderboard(self):
        self.screen.fill(DARK_GREY)
        title_txt = pygame.font.SysFont('Arial', 50).render("BESTENLISTE", True, GOLDEN)
        self.screen.blit(title_txt, (WINDOW_WIDTH//2 - title_txt.get_width()//2, 50))
        y_pos = 150
        if not self.leaderboard:
            none_txt = pygame.font.SysFont('Arial', 30).render("Keine Einträge vorhanden", True, WHITE)
            self.screen.blit(none_txt, (WINDOW_WIDTH//2 - none_txt.get_width()//2, y_pos))
        else:
            for i, (name, score) in enumerate(self.leaderboard[:10]):
                col = GOLDEN if i == 0 else ((192, 192, 192) if i == 1 else (205, 127, 50) if i == 2 else WHITE)
                entry_txt = pygame.font.SysFont('Arial', 30).render(f"{i+1}. {name}: {score}", True, col)
                self.screen.blit(entry_txt, (WINDOW_WIDTH//2 - 150, y_pos))
                y_pos += 40
        back_btn = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT - 80, 200, 60, "ZURÜCK", color=PURPLE, action=lambda: self.confirm_back_to_main())
        back_btn.draw(self.screen)
        for event in pygame.event.get():
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

if __name__ == "__main__":
    game = Game()
    game.run()


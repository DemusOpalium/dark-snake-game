import pygame
pygame.init()
pygame.display.set_mode((1, 1))  # Temporärer Display für convert_alpha()

# View Scale (Skalierungsfaktor): Passe diesen Wert an (z. B. 1 für klein, 1.5 für mittel, 2 für groß)
VIEW_SCALE = 1.5

# Angepasste Grundwerte basierend auf dem Skalierungsfaktor
GRID_SIZE = int(20 * VIEW_SCALE)
WINDOW_WIDTH = int(750 * VIEW_SCALE)
WINDOW_HEIGHT = int(550 * VIEW_SCALE)
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE
FPS = 60

# Neue Konstanten für UI und Randflächen:
BORDER_SIZE = 20          # Breite/Höhe der Randflächen (links, rechts, unten; ggf. auch oberer Rand am Spielfeld)
UI_CONTAINER_HEIGHT = 50  # Höhe des UI-Bereichs oben

# Farbschema
BLACK = (0, 0, 0)
DARK_GREY = (20, 20, 20)
WHITE = (255, 255, 255)
GREEN = (0, 180, 0)
DARK_GREEN = (0, 80, 0)
RED = (255, 0, 0)
PURPLE = (120, 0, 120)
ORANGE = (255, 140, 0)
GOLDEN = (255, 215, 0)

# Skalierte Schriftarten
try:
    FONT_SMALL = pygame.font.SysFont('Arial', int(20 * VIEW_SCALE))
    FONT_MEDIUM = pygame.font.SysFont('Arial', int(30 * VIEW_SCALE))
    FONT_LARGE = pygame.font.SysFont('Arial', int(50 * VIEW_SCALE))
    FONT_TITLE = pygame.font.SysFont('Arial', int(80 * VIEW_SCALE), bold=True)
except Exception as e:
    FONT_SMALL = pygame.font.Font(None, int(20 * VIEW_SCALE))
    FONT_MEDIUM = pygame.font.Font(None, int(30 * VIEW_SCALE))
    FONT_LARGE = pygame.font.Font(None, int(50 * VIEW_SCALE))
    FONT_TITLE = pygame.font.Font(None, int(80 * VIEW_SCALE))

START_SPEED = 8
MAX_SPEED = 15
PROJECTILE_SPEED_FACTOR = 1.0  # NEW: Projektilgeschwindigkeitsfaktor (Default 1.0)
LEADERBOARD_FILE = "leaderboard.txt"

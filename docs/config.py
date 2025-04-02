import pygame
pygame.init()
pygame.display.set_mode((1,1))  # Temporärer Display für convert_alpha()

WINDOW_WIDTH = 550
WINDOW_HEIGHT = 750
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE
FPS = 60

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

# Schriftarten
try:
    FONT_SMALL = pygame.font.SysFont('Arial', 20)
    FONT_MEDIUM = pygame.font.SysFont('Arial', 30)
    FONT_LARGE = pygame.font.SysFont('Arial', 50)
    FONT_TITLE = pygame.font.SysFont('Arial', 80, bold=True)
except:
    FONT_SMALL = pygame.font.Font(None, 20)
    FONT_MEDIUM = pygame.font.Font(None, 30)
    FONT_LARGE = pygame.font.Font(None, 50)
    FONT_TITLE = pygame.font.Font(None, 80)

START_SPEED = 8
MAX_SPEED = 15
LEADERBOARD_FILE = "leaderboard.txt"


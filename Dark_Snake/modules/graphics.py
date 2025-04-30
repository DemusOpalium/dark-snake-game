
# [KS_TAG: GRAPHICS_INIT]
import os
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, GRID_SIZE

# Einheitliche Ladefunktion für Grafiken aus Kategorieordnern
def load_image(name, category=""):
    path = os.path.join("assets", "graphics", category, name)
    try:
        image = pygame.image.load(path).convert_alpha()
        return image
    except Exception as e:
        print(f"[Fehler] Grafik nicht gefunden: {path} ({e})")
        return pygame.Surface((32, 32), pygame.SRCALPHA)

# Thumbnail-Helper für UI/Inventar
def scale_to_thumbnail(image, factor=0.75):
    if image:
        width = int(GRID_SIZE * factor)
        height = int(GRID_SIZE * factor)
        return pygame.transform.scale(image, (width, height))
    return image

# Snake-Grafiken
SNAKE_HEAD_IMG = load_image("SnakeHeadAlpha1.png")
if SNAKE_HEAD_IMG:
    SNAKE_HEAD_IMG = pygame.transform.scale(SNAKE_HEAD_IMG, (GRID_SIZE, GRID_SIZE))
SNAKE_HEAD1G20 = load_image("SnakeHead1G20.png")
SNAKE_HEAD2G20 = load_image("SnakeHead2G20.png")
SNAKE_HEAD3G20 = load_image("SnakeHead3G20.png")
SNAKE_HEAD_BETA = load_image("SnakeHeadBetaG20.png")
SNAKE_BODY_IMG = load_image("SnakeBodyAlpha1.png")
SNAKE_BODY_BETA = load_image("SnakeBodyBeta.png")
SNAKE_BODY_Body7 = load_image("SnakeBody7.png")
SNAKE_BODY_Body5 = load_image("SnakeBody5.png")
SNAKE_BODY_Body4 = load_image("SnakeBody4.png")
SNAKE_BODY_Body2 = load_image("SnakeBody2.png")
SNAKE_BODY_Body6 = load_image("SnakeBody6.png")

# Projektile
PROJECTILE_IMG = load_image("Projektil.png")
PROJECTILE2_IMG = load_image("Projektil2.png")
PROJECTILE3_IMG = load_image("Projektil3.png")
PROJECTILE4_IMG = load_image("Projektil4.png")
PROJECTILE5_IMG = load_image("Projektil5.png")

# Titelbild
TITLE_IMG = load_image("titel1.png")

# Bosse
BOSS_IMG = load_image("Boss-RingG60.png")
BOSS_ALT_IMG = load_image("Boss-SkullPurPurG60.png")
BOSS_ALEX_IMG = load_image("Boss-AlexG60.png")
BOSS_BOLGI_IMG = load_image("Boss-BolgiG60.png")
BOSS_DEMUS_IMG = load_image("Boss-DemusG60.png")
BOSS_FIN_IMG = load_image("Boss-FinG60.png")
BOSS_GLOBY_IMG = load_image("Boss-GlobyG60.png")
BOSS_NEO_IMG = load_image("Boss-NeoG60.png")

# Portale
PORTAL_IMAGES = [
    load_image("PortalBlauG40.png"),
    load_image("PortalG40.png"),
    load_image("PortalTempelG60.png")
]

ITEM_IMAGES = {
    "FOOD":             load_image("ItemgruenG20.png"),
    "SPEED_BOOST":      load_image("ItemOrangeradG20.png"),
    "SPEED_REDUCTION":  load_image("ItemGrauradG20.png"),
    "SCORE_BOOST":      load_image("ItemblauG20.png"),
    "INVINCIBILITY":    load_image("ItemDiamantG20.png"),
    "LOOT_BOX":         load_image("ItemLavaG20.png"),
    "LENGTH_SHORTENER": load_image("ItemRotradG20.png"),
    "LENGTH_DOUBLE":    load_image("ItemTrank1G20.png"),
    "DICE_EVENT":       load_image("ItemTrank2G20.png"),
    "SPECIAL_DAMAGE":   load_image("ItemTrank3FG20.png"),
    "PROJECTILE_SHOOT": load_image("Projektil.png"),
    "SPAWN_BOLBU":      load_image("SPAWN_BOLBU.png", "items"),
}

# Gegner
ENEMY_TIM_IMG = load_image("gegner-TimG40.png")
ENEMY_SPOONG_IMG = load_image("gegner-SpoongG40.png")
ENEMY_OMNI_IMG = load_image("gegner-OmniG40.png")
ENEMY_GLUBS_IMG = load_image("gegner-glubsG40.png")

# UI
OPTIONS_BUTTON_IMG = load_image("optionsButton1.png")
PLAY_BUTTON_IMG = load_image("PlayButton1.png")

# Tile graphics

TILE_IMAGES = {}
_tile_dir = os.path.join("assets", "graphics", "tiles")
if os.path.isdir(_tile_dir):
    for fname in os.listdir(_tile_dir):
        if fname.lower().endswith(".png"):
            key = os.path.splitext(fname)[0]
            img = load_image(fname, "tiles")
            if img:
                img = pygame.transform.scale(img, (GRID_SIZE, GRID_SIZE))
            TILE_IMAGES[key] = img


# Zugriffsfunktion für Tile
def get_tile(name):
    return TILE_IMAGES.get(name)

# [KS_TAG: GRAPHICS_DICT] – Zentrale Mapping-Struktur
GRAPHICS = {
    "BOLBU_PROJECTILE": load_image("bolbu_projectile.png", "projectiles"),
    "SPAWN_BOLBU": load_image("SPAWN_BOLBU.png", "items")
}

# Zugriffsfunktion für zentrale Grafiken
def get_image(name):
    return GRAPHICS.get(name, pygame.Surface((32, 32), pygame.SRCALPHA))

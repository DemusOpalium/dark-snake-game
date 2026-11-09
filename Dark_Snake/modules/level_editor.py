# modules/level_editor.py – Finales UI-Layout mit breiterem, tieferem Tile-Container
import json, pygame
from config import GRID_WIDTH, GRID_HEIGHT, GRID_SIZE, WINDOW_WIDTH, WINDOW_HEIGHT
from modules.graphics import TILE_IMAGES
from modules.resources import custom_level_path

TOOLBAR_W = 200
BTN_H = 28
ZOOM = 0.72
FAV_ROW_H = 50
TILE_ROW_H = 600
SCROLL_TOP = 275
MAP_TOP = SCROLL_TOP + TILE_ROW_H - 650  # damit Spielfeld darunter bleibt
MAX_FAV = 8


COLOR_BG     = (25, 25, 25)
COLOR_BTN    = (50, 50, 50)
COLOR_FAV    = (70, 70, 70)
COLOR_TEXT   = (255, 255, 255)
COLOR_SELECT = (255, 255, 0)
COLOR_FRAME  = (120, 0, 120)

class LevelEditor:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.drawing = False
        self.tiles = dict(sorted(TILE_IMAGES.items()))
        self.current_tile = list(self.tiles.keys())[0] if self.tiles else None
        self.map = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.undo_stack = []
        self.redo_stack = []
        self.favorites = []
        self.scroll = 0
        self.font = pygame.font.SysFont("Arial", 15)
        self.info = ""
        self.buttons = self._make_buttons()
        self.tile_scroll_offset = 0

    def _make_buttons(self):
        labels = [
            ("Save", self.save_map),
            ("Load", self.load_map),
            ("Sim Start", self.start_sim),
            ("Sim Stop", self.stop_sim),
            ("Rand", self.set_border),
            ("Mittelfeld", self.fill_middle),
            ("Undo", self.undo),
            ("Redo", self.redo),
        ]
        buttons = []
        y = 10
        for label, action in labels:
            rect = pygame.Rect(10, y, TOOLBAR_W - 20, BTN_H)
            buttons.append((label, rect, action))
            y += BTN_H + 4
        return buttons

    def toggle(self):
        self.active = not self.active
        self.info = "Editor geöffnet" if self.active else ""

    def handle_event(self, event):
        if not self.active: return
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if mx < TOOLBAR_W and my < SCROLL_TOP:
                for _, rect, action in self.buttons:
                    if rect.collidepoint((mx, my)):
                        action()
                        return
            elif mx > TOOLBAR_W or my > SCROLL_TOP:
                self.drawing = True
                self._paint(mx, my)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.drawing = False
        elif event.type == pygame.MOUSEMOTION and self.drawing:
            self._paint(*event.pos)
        elif event.type == pygame.MOUSEWHEEL:
            max_scroll = max(0, (len(self.tiles) // 5 - 6) * (GRID_SIZE + 4))
            self.tile_scroll_offset += event.y * 20
            self.tile_scroll_offset = max(-max_scroll, min(0, self.tile_scroll_offset))

    def _paint(self, mx, my):
        if mx < TOOLBAR_W or my < MAP_TOP:
            return
        gx = int((mx - TOOLBAR_W) / (GRID_SIZE * ZOOM))
        gy = int((my - MAP_TOP) / (GRID_SIZE * ZOOM))
        if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT and self.current_tile:
            self._store_undo()
            self.map[gy][gx] = self.current_tile
            self.info = f"{self.current_tile} gesetzt"

    def draw(self, screen):
        if not self.active: return

        pygame.draw.rect(screen, COLOR_BG, (0, 0, TOOLBAR_W, WINDOW_HEIGHT))

        for label, rect, _ in self.buttons:
            pygame.draw.rect(screen, COLOR_BTN, rect)
            text = self.font.render(label, True, COLOR_TEXT)
            screen.blit(text, (rect.x + 6, rect.y + 6))

        pygame.draw.rect(screen, COLOR_FAV, (TOOLBAR_W, 0, WINDOW_WIDTH - TOOLBAR_W, FAV_ROW_H))
        for i, key in enumerate(self.favorites):
            img = self.tiles.get(key)
            if img:
                x = TOOLBAR_W + 10 + i * (GRID_SIZE + 6)
                y = 10
                screen.blit(img, (x, y))
                pygame.draw.rect(screen, COLOR_SELECT, (x, y, GRID_SIZE, GRID_SIZE), 1)

        scroll_area = pygame.Rect(0, SCROLL_TOP, TOOLBAR_W, TILE_ROW_H)
        pygame.draw.rect(screen, (40, 40, 40), scroll_area)
        pygame.draw.rect(screen, COLOR_FRAME, scroll_area, 2)
        screen.set_clip(scroll_area)

        keys = list(self.tiles.keys())
        col_count = 5
        for i, key in enumerate(keys):
            col = i % col_count
            row = i // col_count
            x = 10 + col * (GRID_SIZE + 6)
            y = SCROLL_TOP + 10 + row * (GRID_SIZE + 4) + self.tile_scroll_offset
            img = self.tiles[key]
            screen.blit(img, (x, y))
            rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            if key == self.current_tile:
                pygame.draw.rect(screen, COLOR_SELECT, rect, 2)
            if rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                self.current_tile = key
            if rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[2]:
                if key not in self.favorites and len(self.favorites) < MAX_FAV:
                    self.favorites.append(key)
                    self.info = f"[DEBUG] {key} zu Favoriten hinzugefügt."
        screen.set_clip(None)

        surf = pygame.Surface((GRID_WIDTH * GRID_SIZE, GRID_HEIGHT * GRID_SIZE), pygame.SRCALPHA)
        for y, row in enumerate(self.map):
            for x, tile in enumerate(row):
                if tile in self.tiles:
                    surf.blit(self.tiles[tile], (x * GRID_SIZE, y * GRID_SIZE))
        scaled = pygame.transform.scale(surf, (int(GRID_WIDTH * GRID_SIZE * ZOOM), int(GRID_HEIGHT * GRID_SIZE * ZOOM)))
        screen.blit(scaled, (TOOLBAR_W, MAP_TOP))

        txt = self.font.render(self.info, True, COLOR_SELECT)
        screen.blit(txt, (10, WINDOW_HEIGHT - 24))

    def _store_undo(self):
        self.undo_stack.append(json.loads(json.dumps(self.map)))
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(json.loads(json.dumps(self.map)))
            self.map = self.undo_stack.pop()
            self.info = "Undo"

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(json.loads(json.dumps(self.map)))
            self.map = self.redo_stack.pop()
            self.info = "Redo"

    def fill_middle(self):
        self._store_undo()
        for y in range(1, GRID_HEIGHT-1):
            for x in range(1, GRID_WIDTH-1):
                self.map[y][x] = self.current_tile
        self.info = "Mittelfeld gefüllt"

    def set_border(self):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if x == 0 or y == 0 or x == GRID_WIDTH - 1 or y == GRID_HEIGHT - 1:
                    self.map[y][x] = self.current_tile
        self.info = "Rand gesetzt"

    def save_map(self):
        try:
            with open(custom_level_path(for_write=True), "w", encoding="utf-8") as f:
                json.dump(self.map, f)
        except OSError:
            self.info = "Level konnte nicht gespeichert werden"
            return False
        self.info = "Level gespeichert"
        return True

    def load_map(self):
        try:
            level_map = self.read_map()
            self._store_undo()
            self.map = level_map
            self.info = "Level geladen"
        except (OSError, ValueError):
            self.info = "Level konnte nicht geladen werden"

    def read_map(self):
        with open(custom_level_path(), encoding="utf-8") as f:
            level_map = json.load(f)
        if not isinstance(level_map, list) or len(level_map) != GRID_HEIGHT:
            raise ValueError("Ungültige Level-Höhe")
        for row in level_map:
            if not isinstance(row, list) or len(row) != GRID_WIDTH:
                raise ValueError("Ungültige Level-Breite")
            if any(tile is not None and not isinstance(tile, str) for tile in row):
                raise ValueError("Ungültige Level-Kachel")
        return level_map

    def start_sim(self):
        if not self.save_map():
            return
        self.simulation = True
        self.game.level_map = self.map
        self.game.build_background_from_map()
        self.info = "Sim gestartet"

    def stop_sim(self):
        self.simulation = False
        self.info = "Sim gestoppt"

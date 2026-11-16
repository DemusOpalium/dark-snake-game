"""Practice map and validation for the World Studio learning session."""

from config import GRID_HEIGHT, GRID_WIDTH
from modules.frostage_assets import frostage_assets
from modules.level_drafts import LevelDocument


CENTER_X, CENTER_Y = GRID_WIDTH // 2, GRID_HEIGHT // 2
LEFT, RIGHT = CENTER_X - 6, CENTER_X + 6
TOP, BOTTOM = CENTER_Y - 4, CENTER_Y + 5
FLOOR_CELLS = frozenset((x, y) for x in range(CENTER_X - 4, CENTER_X)
                        for y in (CENTER_Y - 2, CENTER_Y - 1))
OBSTACLE_CELLS = frozenset((CENTER_X + 2, CENTER_Y + offset) for offset in (-2, -1, 1, 3))
ROOF_ANCHORS = frozenset({(CENTER_X + 2, CENTER_Y - 1)})
PROTECTED_CORRIDOR = frozenset((x, y) for x in range(LEFT + 1, RIGHT)
                               for y in (CENTER_Y, CENTER_Y + 2)) | {(CENTER_X, CENTER_Y + 1)}
FLOOR_TARGET = 3
FROST_FLOOR_IDS = frozenset(key for key, asset in frostage_assets().items()
                            if asset.category == "ground" and asset.cells == (1, 1))

_MARKED_CELLS = (FLOOR_CELLS, OBSTACLE_CELLS, ROOF_ANCHORS, FLOOR_CELLS, PROTECTED_CORRIDOR)
_RESET_AREAS = (("ground", FLOOR_CELLS), ("collision", OBSTACLE_CELLS), ("roof", ROOF_ANCHORS), None, None)


def is_frost_floor(asset_id):
    return asset_id in FROST_FLOOR_IDS


def practice_document():
    """Return a new practice draft with open routes from both native spawn cells."""
    graphics = [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
    collisions = {}
    for y in range(TOP, BOTTOM + 1):
        for x in range(LEFT, RIGHT + 1):
            if x in (LEFT, RIGHT) or y in (TOP, BOTTOM):
                graphics[y][x] = "frozenbase_1_0"
                collisions[x, y] = "WALL"
            else:
                graphics[y][x] = "frosthauch_3_0" if (x, y) in PROTECTED_CORRIDOR else "frozenbase_0_0"
    return LevelDocument(graphics, collision=collisions)


def _practice_roof(roofs):
    for anchor in ROOF_ANCHORS:
        item = roofs.get(anchor)
        asset = frostage_assets().get(item.asset_id) if item is not None else None
        if asset is not None and asset.category == "roof" and (item.width, item.height) == asset.cells:
            return anchor, item
    return None


class Tutorial:
    """Track the interaction-only steps and recheck authored work on demand."""

    def __init__(self):
        self.step_index = 0
        self.example_visible = False
        self._roof_hidden = None
        self._roof_shown = None
        self._lock_trial = False
        self._locked_attempt = False
        self._lock_done = False
        self._played_1p = False

    @property
    def marked_cells(self):
        return _MARKED_CELLS[self.step_index]

    @property
    def reset_cells(self):
        return _RESET_AREAS[self.step_index]

    def progress(self, editor):
        floor = sum(is_frost_floor(editor.map[y][x]) for x, y in FLOOR_CELLS) >= FLOOR_TARGET
        obstacle = (any(editor.collisions.get(cell) == "WALL" for cell in OBSTACLE_CELLS)
                    and PROTECTED_CORRIDOR.isdisjoint(editor.collisions))
        roof = (self._roof_shown is not None and _practice_roof(editor.roofs) == self._roof_shown
                and editor.layer_visible("roof"))
        unlocked = self._lock_done and not editor.layer_locked("ground")
        return floor, obstacle, roof, unlocked, self._played_1p

    def finished(self, editor):
        return self.step_index == len(_MARKED_CELLS) - 1 and all(self.progress(editor))

    def next(self, editor):
        if self.step_index == len(_MARKED_CELLS) - 1 or not all(self.progress(editor)[:self.step_index + 1]):
            return False
        self.step_index += 1
        self.example_visible = False
        return True

    def previous(self):
        if self.step_index == 0:
            return False
        self.step_index -= 1
        self.example_visible = False
        return True

    def retry(self):
        """Clear the current step's observations after the editor resets its practice cells."""
        self.example_visible = False
        if self.step_index == 2:
            self._roof_hidden = self._roof_shown = None
        elif self.step_index == 3:
            self._lock_trial = self._locked_attempt = self._lock_done = False
        elif self.step_index == 4:
            self._played_1p = False

    def toggle_example(self):
        self.example_visible = not self.example_visible

    def roof_visibility_changed(self, visible, roofs):
        if self.step_index != 2:
            return
        roof = _practice_roof(roofs)
        if not visible:
            self._roof_hidden = roof
        elif roof is not None and roof == self._roof_hidden:
            self._roof_shown = roof

    def layer_lock_changed(self, layer, locked):
        if self.step_index != 3 or layer != "ground":
            return
        if locked:
            self._lock_trial = True
            self._locked_attempt = False
        elif self._lock_trial:
            self._lock_done |= self._locked_attempt
            self._lock_trial = False

    def blocked_edit(self, layer):
        if self.step_index == 3 and layer == "ground" and self._lock_trial:
            self._locked_attempt = True

    def playtest_started(self, player_count):
        if self.step_index == 4 and player_count == 1:
            self._played_1p = True

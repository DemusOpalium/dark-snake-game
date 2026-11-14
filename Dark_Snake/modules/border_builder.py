"""Plan changes to the ground tiles on a map's outer edges."""

from dataclasses import dataclass, field


SIDES = ("left", "right", "top", "bottom")
_CORNER_SIDES = {
    "top_left": ("top", "left"),
    "top_right": ("top", "right"),
    "bottom_left": ("bottom", "left"),
    "bottom_right": ("bottom", "right"),
}
CORNERS = tuple(_CORNER_SIDES)


@dataclass(frozen=True, slots=True)
class BorderCell:
    x: int
    y: int
    previous: str | None
    tile: str
    source: str

    @property
    def changed(self):
        return self.previous != self.tile

    @property
    def overwrites(self):
        return self.previous is not None and self.changed


@dataclass(slots=True)
class BorderPlan:
    """Choose the participating sides and optional overrides for their corners."""

    sides: dict[str, str | None] = field(default_factory=dict)
    corners: dict[str, str | None] = field(default_factory=dict)

    def corner_choice(self, corner):
        """Return the tile and its source, preferring the horizontal side by default."""
        horizontal, vertical = _CORNER_SIDES[corner]
        for side in (horizontal, vertical):
            if (tile := self.sides.get(side)) is not None:
                override = self.corners.get(corner)
                return (override, corner) if override is not None else (tile, side)
        return None

    def preview(self, level_map):
        """Read the targeted cells, including ones whose tiles would stay the same."""
        last_y = len(level_map) - 1
        last_x = len(level_map[0]) - 1
        cells = []
        for side, x in (("left", 0), ("right", last_x)):
            if (tile := self.sides.get(side)) is not None:
                cells.extend(BorderCell(x, y, level_map[y][x], tile, side) for y in range(1, last_y))
        for side, y in (("top", 0), ("bottom", last_y)):
            if (tile := self.sides.get(side)) is not None:
                cells.extend(BorderCell(x, y, level_map[y][x], tile, side) for x in range(1, last_x))
        positions = ((0, 0), (last_x, 0), (0, last_y), (last_x, last_y))
        for corner, (x, y) in zip(CORNERS, positions):
            if (choice := self.corner_choice(corner)) is not None:
                tile, source = choice
                cells.append(BorderCell(x, y, level_map[y][x], tile, source))
        return tuple(sorted(cells, key=lambda cell: (cell.y, cell.x)))

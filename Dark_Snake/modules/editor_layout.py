"""Window geometry and a grid camera for World Studio."""

import pygame

from config import GRID_HEIGHT, GRID_WIDTH


MIN_STUDIO_SIZE = (900, 620)
PANEL_GAP = 8
HEADER_HEIGHT = 88
STATUS_HEIGHT = 48
MAX_CELL_SIZE = 90
ZOOM_FACTOR = 1.25


class StudioLayout:
    def __init__(self, size, *, show_library=True, show_inspector=True):
        width, height = size
        self.bounds = pygame.Rect(0, 0, width, height)
        header_height = min(HEADER_HEIGHT, height // 3)
        status_height = min(STATUS_HEIGHT, height // 4)
        self.header = pygame.Rect(0, 0, width, header_height)
        self.status = pygame.Rect(0, height - status_height, width, status_height)

        gap_x = min(PANEL_GAP, width // 8)
        gap_y = min(PANEL_GAP, max(0, (height - header_height - status_height - 1) // 2))
        top = self.header.bottom + gap_y
        panel_height = max(0, self.status.top - gap_y - top)
        side_limit = max(0, (width - 4 * gap_x) // 3)
        library_width = min(max(196, width // 5), 288, side_limit) if show_library else 0
        inspector_width = min(max(192, width // 5), 288, side_limit) if show_inspector else 0
        self.library = pygame.Rect(gap_x, top, library_width, panel_height)
        self.inspector = pygame.Rect(width - gap_x - inspector_width, top, inspector_width, panel_height)

        left = self.library.right + gap_x if library_width else gap_x
        right = self.inspector.left - gap_x if inspector_width else width - gap_x
        self.viewport = pygame.Rect(left, top, max(0, right - left), panel_height)


class MapCamera:
    """Project saved grid coordinates onto the current editor viewport."""

    def __init__(self, viewport):
        self.viewport = pygame.Rect(viewport)
        self.reset()

    @property
    def _fit_cell_size(self):
        return max(1, min(self.viewport.width // GRID_WIDTH, self.viewport.height // GRID_HEIGHT))

    def reset(self):
        self.cell_size = self._fit_cell_size
        self.board_rect = pygame.Rect((0, 0), (GRID_WIDTH * self.cell_size, GRID_HEIGHT * self.cell_size))
        self.board_rect.center = self.viewport.center
        self._clamp_position()

    def set_viewport(self, viewport):
        viewport = pygame.Rect(viewport)
        if viewport == self.viewport:
            return
        fit_view = self.cell_size == self._fit_cell_size
        focus = self.viewport.center
        self.viewport = viewport
        if fit_view:
            self.reset()
        else:
            self._place_board(focus, viewport.center, max(self.cell_size, self._fit_cell_size))

    def cell_at(self, position):
        if not self.viewport.collidepoint(position) or not self.board_rect.collidepoint(position):
            return None
        return ((position[0] - self.board_rect.left) // self.cell_size,
                (position[1] - self.board_rect.top) // self.cell_size)

    def zoom_at(self, position, steps):
        """Zoom around a pointer position without changing any grid coordinates."""
        if not steps or not self.viewport.collidepoint(position):
            return False
        minimum = self._fit_cell_size
        maximum = max(minimum, MAX_CELL_SIZE)
        scale = ZOOM_FACTOR ** max(-30, min(30, steps))
        new_size = round(self.cell_size * scale)
        if new_size == self.cell_size:
            new_size += 1 if steps > 0 else -1
        new_size = min(maximum, max(minimum, new_size))
        if self.cell_size == new_size:
            return False
        position = (
            min(max(self.board_rect.left, position[0]), self.board_rect.right - 1),
            min(max(self.board_rect.top, position[1]), self.board_rect.bottom - 1),
        )
        self._place_board(position, position, new_size)
        return True

    def pan(self, dx, dy):
        """Move a zoomed view, keeping the board reachable at both extremes."""
        start = self.board_rect.topleft
        self.board_rect.move_ip(dx, dy)
        self._clamp_position()
        return self.board_rect.topleft != start

    def _place_board(self, focus, position, cell_size):
        offset_x = (focus[0] - self.board_rect.left) * cell_size // self.cell_size
        offset_y = (focus[1] - self.board_rect.top) * cell_size // self.cell_size
        self.cell_size = cell_size
        self.board_rect.size = GRID_WIDTH * cell_size, GRID_HEIGHT * cell_size
        self.board_rect.topleft = position[0] - offset_x, position[1] - offset_y
        self._clamp_position()

    def _clamp_position(self):
        board, viewport = self.board_rect, self.viewport
        if board.width <= viewport.width:
            board.centerx = viewport.centerx
        else:
            board.left = max(viewport.right - board.width, min(viewport.left, board.left))
        if board.height <= viewport.height:
            board.centery = viewport.centery
        else:
            board.top = max(viewport.bottom - board.height, min(viewport.top, board.top))

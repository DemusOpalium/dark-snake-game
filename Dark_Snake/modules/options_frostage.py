"""FrostAge presentation for the existing OptionsMenu; never owns game settings.

The view reuses the original widgets and their callbacks. It only assigns
rectangles, draws them in a quieter theme and caches scaled images.
"""
from __future__ import annotations

import math
import time

import pygame

from modules.main_menu import cover_background


INK = (11, 17, 31)
PANEL = (17, 27, 44)
PANEL_INNER = (12, 21, 37)
BORDER = (82, 124, 155)
FROST = (173, 225, 239)
TEXT = (234, 242, 247)
MUTED = (157, 181, 197)
HIGHLIGHT = (111, 204, 225)
TRACK = (36, 52, 68)


def _label(surface, font, message, x, y, color=TEXT, max_width=None):
    """Trim only the painted label, never the stored string or filename."""
    value = str(message)
    if max_width is not None:
        while value and font.size(value)[0] > max_width:
            value = value[:-2] + "…" if len(value) > 2 else ""
    if value:
        surface.blit(font.render(value, True, color), (x, y))


def snake_preview_positions(stage, cell_size, step, elapsed_seconds, *,
                            body_count=5, speed=32, phase=0):
    """Head first, body behind it, all on a single continuous horizontal track.

    Travel starts one sprite-width outside left and wraps only once the last
    body segment has exited right. Returning rectangles rather than pixels
    keeps visual tests deterministic and prevents stretched body spacing.
    """
    travel = stage.width + body_count * step + 2 * cell_size
    distance = (max(0.0, elapsed_seconds) * speed + phase) % travel
    head_x = stage.left - cell_size + round(distance)
    y = stage.centery - cell_size // 2
    return tuple(
        pygame.Rect(head_x - index * step, y, cell_size, cell_size)
        for index in range(body_count + 1)
    )


class FrostAgeOptionsView:
    def __init__(self, menu):
        self.menu = menu
        self.size = None
        self.background = None
        self._sprite_cache = {}
        self._thumb_cache = {}
        self._music_scroll = 0
        self._preview_epoch = time.monotonic()
        self._source_background = getattr(
            getattr(menu.game, "main_menu", None), "_background_source", None
        )
        self._fonts = {}

    def _font(self, size, bold=False):
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont("Arial", size, bold=bold)
        return self._fonts[key]

    def layout(self, size):
        size = tuple(size)
        if size == self.size:
            return
        self.size = size
        width, height = size
        margin = max(9, round(width * .012))
        gap = max(9, round(width * .009))
        top = 124 if height >= 760 else 105
        usable = width - 2 * margin - 2 * gap
        left_w = round(usable * .32)
        mid_w = round(usable * .38)
        right_w = usable - left_w - mid_w
        panel_h = max(100, height - top - margin)
        m = self.menu
        m.settings_panel.rect = pygame.Rect(margin, top, left_w, panel_h)
        m.inventory_panel.rect = pygame.Rect(margin + left_w + gap, top, mid_w, panel_h)
        m.preview_panel.rect = pygame.Rect(
            margin + left_w + gap + mid_w + gap, top, right_w, panel_h
        )
        m.control_panel.rect = pygame.Rect(margin, 54, width - 2 * margin, 50)
        action_gap = 10
        action_w = (m.control_panel.rect.width - 3 * action_gap) // 4
        for index, button in enumerate((
            m.save_btn, m.back_btn, m.assign_p1_btn, m.assign_p2_btn
        )):
            button.rect = pygame.Rect(
                margin + index * (action_w + action_gap),
                61 if height >= 760 else 60,
                action_w, 43 if height >= 760 else 35,
            )
        game_h = int(panel_h * .56)
        inner = max(12, int(left_w * .044))
        m.gameplay_container.rect = pygame.Rect(
            margin + inner, top + 43, left_w - inner * 2, game_h - 49
        )
        m.audio_container.rect = pygame.Rect(
            margin + inner, top + game_h + 8, left_w - inner * 2,
            panel_h - game_h - 19,
        )
        slider_w = max(60, left_w - inner * 2 - 18)
        slider_x = margin + inner + 9
        first = top + (76 if height >= 760 else 63)
        step = max(42, int((game_h - (94 if height >= 760 else 79)) / 4))
        for index, slider in enumerate((
            m.speed_slider, m.difficulty_slider, m.projectile_slider,
            m.spawnrate_slider, m.boss_health_slider
        )):
            slider.rect = pygame.Rect(slider_x, first + index * step, slider_w, 12)
            slider.handle_rect = pygame.Rect(slider.get_handle_x(), slider.rect.y - 6, 15, 24)
        audio_top = m.audio_container.rect.top
        audio_step = 58 if height >= 760 else 42
        for index, slider in enumerate((m.music_slider, m.sfx_slider)):
            slider.rect = pygame.Rect(slider_x, audio_top + 52 + index * audio_step, slider_w, 12)
            slider.handle_rect = pygame.Rect(slider.get_handle_x(), slider.rect.y - 6, 15, 24)
        if m.music_dropdown is not None:
            m.music_dropdown.rect = pygame.Rect(
                slider_x, min(audio_top + 55 + 2 * audio_step, top + panel_h - 48),
                slider_w, 34
            )
        tab_x = m.inventory_panel.rect.left + 15
        tab_y = top + 43
        tab_gap = 8
        tab_w = (mid_w - 30 - tab_gap) // 2
        m.head_tab_button.rect = pygame.Rect(tab_x, tab_y, tab_w, 36)
        m.body_tab_button.rect = pygame.Rect(tab_x + tab_w + tab_gap, tab_y, tab_w, 36)
        m.inventory_grid_rect = pygame.Rect(
            tab_x, tab_y + 48, mid_w - 30, panel_h - 106
        )
        right = m.preview_panel.rect
        preview_gap = 14
        area_h = (right.height - 64 - preview_gap) // 2
        m.final_preview_p1.rect = pygame.Rect(
            right.x + 14, right.y + 45, right.width - 28, area_h
        )
        m.final_preview_p2.rect = pygame.Rect(
            right.x + 14, right.y + 45 + area_h + preview_gap,
            right.width - 28, area_h
        )
        self.clamp_scroll()
        self.background = None  # rebuilt only if the viewport dimensions change

    def clamp_scroll(self):
        grid = self.menu.inventory_grid_rect
        options = self.menu.head_options if self.menu.current_tab == "Heads" else self.menu.body_options
        cell = max(1, (grid.width - 5 * 10) // 4)
        rows = math.ceil(len(options) / 4)
        content_height = rows * (cell + 10) + 10
        max_scroll = max(0, content_height - grid.height)
        self.menu.inventory_scroll_offset = max(
            -max_scroll, min(0, self.menu.inventory_scroll_offset)
        )

    def _backdrop(self):
        if self.background is not None:
            return self.background
        if self._source_background is not None:
            bg = cover_background(self._source_background, self.size)
        else:
            bg = pygame.Surface(self.size)
            bg.fill(INK)
        shade = pygame.Surface(self.size, pygame.SRCALPHA)
        shade.fill((5, 13, 27, 220))
        bg.blit(shade, (0, 0))
        self.background = bg
        return bg

    def _panel(self, surface, rect, title):
        pygame.draw.rect(surface, PANEL, rect, border_radius=11)
        pygame.draw.rect(surface, BORDER, rect, 2, border_radius=11)
        pygame.draw.line(surface, (48, 80, 105),
                         (rect.left + 10, rect.top + 43),
                         (rect.right - 10, rect.top + 43), 1)
        small = self.size[0] < 1100
        _label(surface, self._font(17 if small else 20, True),
               title, rect.left + 15, rect.top + 10, FROST, rect.width - 26)

    def _button(self, surface, button, active=False):
        r = button.rect
        fill = (38, 72, 94) if button.is_hovered or active else PANEL_INNER
        stroke = HIGHLIGHT if button.is_hovered or active else BORDER
        pygame.draw.rect(surface, fill, r, border_radius=7)
        pygame.draw.rect(surface, stroke, r, 2, border_radius=7)
        font = self._font(16 if self.size[0] < 1100 else 19, True)
        caption = button.text
        while caption and font.size(caption)[0] > r.width - 14:
            caption = caption[:-2] + "…" if len(caption) > 2 else ""
        if caption:
            txt = font.render(caption, True, TEXT)
            surface.blit(txt, txt.get_rect(center=r.center))

    def _slider(self, surface, slider, label, value):
        r = slider.rect
        font = self._font(14 if self.size[0] < 1100 else 17)
        _label(surface, font, f"{label}: {value}", r.x, r.y - 25,
               TEXT, r.width)
        pygame.draw.rect(surface, TRACK, r, border_radius=5)
        percent = max(0., min(1., (slider.current_val - slider.min_val) /
                             (slider.max_val - slider.min_val)))
        fill = pygame.Rect(r.left, r.top, round(percent * r.width), r.height)
        if fill.width:
            pygame.draw.rect(surface, HIGHLIGHT, fill, border_radius=4)
        handle_x = min(r.right - 2, max(r.left, slider.handle_rect.x + 5))
        pygame.draw.circle(surface, TEXT, (handle_x, r.centery), 9)

    def _music_popup(self):
        dropdown = self.menu.music_dropdown
        if dropdown is None:
            return None
        count = min(len(dropdown.options), 5)
        row_h = 30 if self.size[0] < 1100 else 34
        total_h = count * row_h
        parent = self.menu.settings_panel.rect
        y = (dropdown.rect.bottom + 3 if dropdown.rect.bottom + total_h < parent.bottom - 8
             else dropdown.rect.top - total_h - 3)
        return pygame.Rect(dropdown.rect.x, y, dropdown.rect.width, total_h), row_h

    def handle_music_event(self, event):
        """A bounded popup avoids the legacy dropdown drawing outside the window."""
        dropdown = self.menu.music_dropdown
        if dropdown is None:
            return False
        if event.type == pygame.KEYDOWN and dropdown.expanded:
            if event.key == pygame.K_ESCAPE:
                dropdown.expanded = False
                return True
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                delta = -1 if event.key == pygame.K_UP else 1
                self._music_scroll = max(
                    0, min(max(0, len(dropdown.options) - 5), self._music_scroll + delta)
                )
                return True
        if event.type == pygame.MOUSEWHEEL and dropdown.expanded:
            self._music_scroll = max(
                0, min(max(0, len(dropdown.options) - 5),
                       self._music_scroll - event.y)
            )
            return True
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return False
        pos = event.pos
        if dropdown.rect.collidepoint(pos):
            dropdown.expanded = not dropdown.expanded
            self._music_scroll = max(
                0, min(dropdown.selected_index, max(0, len(dropdown.options) - 5))
            )
            return True
        if dropdown.expanded:
            popup, row_h = self._music_popup()
            if popup.collidepoint(pos):
                index = self._music_scroll + (pos[1] - popup.top) // row_h
                if 0 <= index < len(dropdown.options):
                    dropdown.selected_index = index
                    dropdown.callback(dropdown.options[index])
                dropdown.expanded = False
                return True
            dropdown.expanded = False
        return False

    def _draw_music(self, surface):
        dropdown = self.menu.music_dropdown
        if dropdown is None:
            return
        r = dropdown.rect
        pygame.draw.rect(surface, PANEL_INNER, r, border_radius=5)
        pygame.draw.rect(surface, BORDER, r, 1, border_radius=5)
        font = self._font(13 if self.size[0] < 1100 else 15)
        title = dropdown.options[dropdown.selected_index]
        _label(surface, font, title, r.left + 10, r.top + 8,
               TEXT, r.width - 42)
        pygame.draw.polygon(surface, FROST, [
            (r.right - 24, r.top + 13), (r.right - 10, r.top + 13),
            (r.right - 17, r.top + 21)
        ])

    def _draw_music_popup(self, surface):
        dropdown = self.menu.music_dropdown
        if dropdown is None or not dropdown.expanded:
            return
        popup, row_h = self._music_popup()
        pygame.draw.rect(surface, INK, popup)
        pygame.draw.rect(surface, HIGHLIGHT, popup, 2)
        font = self._font(13 if self.size[0] < 1100 else 15)
        for row in range(popup.height // row_h):
            index = self._music_scroll + row
            if index >= len(dropdown.options):
                break
            line = pygame.Rect(popup.x + 2, popup.y + row * row_h,
                               popup.width - 4, row_h)
            if index == dropdown.selected_index:
                pygame.draw.rect(surface, (40, 75, 99), line)
            _label(surface, font, dropdown.options[index],
                   line.x + 8, line.y + 6, TEXT, line.width - 16)

    def _image(self, tab, filename, size):
        if not filename:
            return None
        key = (tab, filename, size)
        if key not in self._sprite_cache:
            original = self.menu.get_skin_image(tab, filename)
            self._sprite_cache[key] = (
                pygame.transform.smoothscale(original, (size, size))
                if original is not None else None
            )
        return self._sprite_cache[key]

    def _preview_sprite(self, tab, filename, size, player):
        """Match the real in-game fallback for players with no custom skin."""
        image = self._image(tab, filename, size)
        if image is not None:
            return image
        from modules.graphics import SNAKE_BODY_IMG, SNAKE_HEAD_BETA, SNAKE_HEAD_IMG

        key = ("default", tab, player if tab == "Heads" else 0, size)
        if key not in self._sprite_cache:
            source = (SNAKE_BODY_IMG if tab == "Bodies" else
                      (SNAKE_HEAD_BETA if player == 2 else SNAKE_HEAD_IMG))
            self._sprite_cache[key] = pygame.transform.smoothscale(
                source, (size, size)
            )
        return self._sprite_cache[key]

    def _draw_moving_snake(self, surface, rect, player, head, body,
                           image_top, image_size):
        """Decorative 6-segment Snake: fixed track, no game-state updates."""
        top = image_top + image_size + 9
        available = rect.bottom - 69 - top
        if available < 25:
            return
        stage = pygame.Rect(rect.x + 14, top, rect.width - 28,
                            min(90, available))
        if stage.width < 80:
            return
        pygame.draw.rect(surface, (10, 27, 43), stage, border_radius=7)
        pygame.draw.rect(surface, BORDER, stage, 1, border_radius=7)

        sprite_size = max(16, min(39, stage.height - 8, stage.width // 7))
        step = max(1, round(sprite_size * .83))  # overlap transparent sprite edges
        if stage.height >= 58:
            _label(surface, self._font(12), "BEWEGTE VORSCHAU · ZOOM",
                   stage.x + 9, stage.y + 5, MUTED, stage.width - 18)
        sprite_head = self._preview_sprite("Heads", head, sprite_size, player)
        sprite_body = self._preview_sprite("Bodies", body, sprite_size, player)
        elapsed = time.monotonic() - self._preview_epoch
        segments = snake_preview_positions(
            stage, sprite_size, step, elapsed, phase=stage.width * (.64 if player == 1 else .34)
        )
        # A single connected chain. Render tail first, head on top.
        previous_clip = surface.get_clip()
        surface.set_clip(stage.inflate(-2, -2).clip(previous_clip))
        for index in range(len(segments) - 1, -1, -1):
            surface.blit(sprite_head if index == 0 else sprite_body,
                         segments[index])
        surface.set_clip(previous_clip)

    def _draw_gallery(self, surface):
        m = self.menu
        grid = m.inventory_grid_rect
        self.clamp_scroll()
        pygame.draw.rect(surface, PANEL_INNER, grid, border_radius=6)
        previous_clip = surface.get_clip()
        surface.set_clip(grid)
        spacing = 10
        cell = max(1, (grid.width - 5 * spacing) // 4)
        options = m.head_options if m.current_tab == "Heads" else m.body_options
        for index, (filename, _, original) in enumerate(options):
            col, row = index % 4, index // 4
            x = grid.x + spacing + col * (cell + spacing)
            y = grid.y + spacing + row * (cell + spacing) + m.inventory_scroll_offset
            rect = pygame.Rect(x, y, cell, cell)
            if rect.bottom < grid.top or rect.top > grid.bottom:
                continue
            key = (m.current_tab, filename, cell)
            if key not in self._thumb_cache:
                self._thumb_cache[key] = pygame.transform.smoothscale(original, (cell, cell))
            surface.blit(self._thumb_cache[key], rect)
            if m.current_selected_img and m.current_selected_img[0] == filename:
                pygame.draw.rect(surface, HIGHLIGHT, rect, 3, border_radius=5)
            elif rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surface, MUTED, rect, 1, border_radius=5)
        surface.set_clip(previous_clip)
        pygame.draw.rect(surface, BORDER, grid, 1, border_radius=6)
        hint_font = self._font(12 if self.size[0] < 1100 else 14)
        _label(surface, hint_font, "Bild wählen · Für P1/P2 übernehmen · Speichern",
               grid.x, grid.bottom + 8, MUTED, grid.width)

    def _draw_preview(self, surface, rect, player, head, body):
        pygame.draw.rect(surface, PANEL_INNER, rect, border_radius=9)
        pygame.draw.rect(surface, BORDER, rect, 1, border_radius=9)
        compact = self.size[1] < 760
        font = self._font(16 if compact else 20, True)
        _label(surface, font, f"SPIELER {player}", rect.x + 14, rect.y + 10,
               FROST, rect.width - 28)
        small = self._font(12 if compact else 14)
        _label(surface, small, "DETAILVORSCHAU · 2×",
               rect.x + 14, rect.y + 41, MUTED, rect.width - 28)
        display_size = 44 if compact else 64
        sprite_gap = 9
        head_img = self._image("Heads", head, display_size)
        body_img = self._image("Bodies", body, display_size)
        images = [img for img in (head_img, body_img) if img is not None]
        top_y = min(rect.bottom - display_size - 45, rect.y + (56 if compact else 82))
        total = len(images) * display_size + max(0, len(images) - 1) * sprite_gap
        at_x = rect.centerx - total // 2
        for img in images:
            surface.blit(img, (at_x, top_y))
            at_x += display_size + sprite_gap
        if not images:
            _label(surface, small, "Noch kein Skin gewählt",
                   rect.left + 14, top_y + 10, MUTED, rect.width - 28)
        self._draw_moving_snake(surface, rect, player, head, body,
                                top_y, display_size)
        # This row uses the unchanged GRID_SIZE from config: genuine in-game scale.
        from config import GRID_SIZE
        _label(surface, small, f"IM SPIEL · {GRID_SIZE} px",
               rect.x + 14, rect.bottom - 61, MUTED, rect.width - 28)
        actual = [self._preview_sprite(tab, name, GRID_SIZE, player)
                  for tab, name in (("Heads", head), ("Bodies", body))]
        actual = [img for img in actual if img is not None]
        x = rect.centerx - (len(actual) * GRID_SIZE + max(0, len(actual)-1) * 6) // 2
        for img in actual:
            surface.blit(img, (x, rect.bottom - 43))
            x += GRID_SIZE + 6

    def draw(self, surface):
        self.layout(surface.get_size())
        m = self.menu
        surface.blit(self._backdrop(), (0, 0))
        big = self._font(21 if self.size[0] < 1100 else 28, True)
        _label(surface, big, "DARK SNAKE   /   FROSTAGE OPTIONS",
               m.settings_panel.rect.left, 13, TEXT, self.size[0] - 20)
        for button in (m.save_btn, m.back_btn, m.assign_p1_btn, m.assign_p2_btn):
            self._button(surface, button)
        self._panel(surface, m.settings_panel.rect, "SPIELREGELN & AUDIO")
        self._panel(surface, m.inventory_panel.rect, "SNAKE-GALERIE")
        self._panel(surface, m.preview_panel.rect, "SPIELERVORSCHAU")
        game_y = m.settings_panel.rect.y + int(m.settings_panel.rect.height * .56)
        pygame.draw.line(surface, BORDER,
                         (m.settings_panel.rect.x + 12, game_y),
                         (m.settings_panel.rect.right - 12, game_y))
        sliders = (
            (m.speed_slider, "Speed", f"{m.speed_slider.current_val:.1f}"),
            (m.difficulty_slider, "Difficulty", f"{m.difficulty_slider.current_val:.1f}"),
            (m.projectile_slider, "Projectile", f"{m.projectile_slider.current_val:.2f}"),
            (m.spawnrate_slider, "Spawnrate", f"{m.spawnrate_slider.current_val:.3f}"),
            (m.boss_health_slider, "Boss HP", f"{m.boss_health_slider.current_val:.1f}"),
            (m.music_slider, "Musik", f"{m.music_slider.current_val:.0%}"),
            (m.sfx_slider, "Soundeffekte", f"{m.sfx_slider.current_val:.0%}"),
        )
        for slider, label, value in sliders:
            self._slider(surface, slider, label, value)
        if m.music_dropdown is not None:
            _label(surface, self._font(12 if self.size[0] < 1100 else 14),
                   "MUSIKTITEL", m.music_dropdown.rect.x,
                   m.music_dropdown.rect.y - 21, MUTED)
            self._draw_music(surface)
        self._button(surface, m.head_tab_button, m.current_tab == "Heads")
        self._button(surface, m.body_tab_button, m.current_tab == "Bodies")
        self._draw_gallery(surface)
        self._draw_preview(surface, m.final_preview_p1.rect, 1,
                           m.selected_head_p1, m.selected_body_p1)
        self._draw_preview(surface, m.final_preview_p2.rect, 2,
                           m.selected_head_p2, m.selected_body_p2)
        # Popup last so it stays above the remaining controls.
        self._draw_music_popup(surface)

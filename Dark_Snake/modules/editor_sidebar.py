"""The World Studio workspace for properties, layers, and map inspection."""

from collections.abc import Callable
from dataclasses import dataclass

import pygame

from modules.graphic_objects import object_anchor_at


PANEL = (24, 33, 48)
BUTTON = (30, 44, 61)
HOVER = (39, 59, 78)
ACTIVE = (27, 59, 79)
STROKE = (61, 87, 111)
TEXT = (232, 240, 250)
MUTED = (162, 180, 200)
FOCUS = (118, 214, 246)
TABS = (
    ("properties", "Eigenschaften"),
    ("layers", "Ebenen"),
    ("cell", "Zelle"),
    ("help", "Hilfe"),
    ("learn", "Lernen"),
)
TAB_IDS = frozenset(key for key, _ in TABS)
GRAPHIC_LAYERS = {"ground": "Boden", "objects": "Objekte", "roof": "Dach / Foreground"}


@dataclass(frozen=True, slots=True)
class _Entry:
    title: str
    detail: str = ""
    action: Callable[[], None] | None = None
    active: bool = False


def _tool_name(editor):
    if editor.inspect_mode:
        return "Zellen ansehen"
    if editor._transferring_roof:
        return "Auf Dachebene verschieben"
    if editor._moving_objects:
        return "Objekt verschieben"
    return {
        "graphics": "Nur Grafik",
        "combined": "Grafik + Kollision",
        "collision": editor.collision_type,
        "damage": "Schaden",
        "slow": "Slow",
    }[editor.placement_mode]


def _damage_detail(damage):
    def seconds(value):
        return format(value, "g").replace(".", ",") + " s"

    duration = "Keine Zeitgrenze" if damage.duration is None else f"Dauer {seconds(damage.duration)}"
    return f"{damage.amount} HP je {seconds(damage.interval)} · {duration}"


def _art_name(editor, key):
    asset = editor.frost_assets.get(key)
    return asset.name if asset is not None else key


class StudioSidebar:
    """Present the existing editor tools in one switchable right-hand pane."""

    def __init__(self, font):
        self.font = font
        self.tab = "properties"
        self._scroll = 0
        self._hover = None

    def show(self, tab):
        if tab not in TAB_IDS:
            raise ValueError(f"Unbekannte Seitenansicht: {tab}")
        if tab != self.tab:
            self.tab = tab
            self._scroll = 0

    def _properties(self, editor, editing):
        mode = editor.placement_mode
        layer = GRAPHIC_LAYERS[editor.graphic_layer]
        if mode in ("damage", "slow"):
            layer = "Effekte"
        elif mode == "collision":
            layer = "Kollisionen"
        entries = [_Entry("Aktives Werkzeug", f"{_tool_name(editor)} · {layer}")]
        item = editor._selected_object()
        has_tile = editor.graphic_layer == "ground" and editor.current_tile in editor.tiles
        if mode in ("graphics", "combined") and (has_tile or item is not None):
            size = f" · {item.width} × {item.height}" if item is not None else ""
            entries.append(_Entry("Gewählte Grafik", f"{_art_name(editor, editor.current_tile)}{size}"))
        if mode in ("damage", "slow"):
            entries.extend((
                _Entry("Schaden", _damage_detail(editor.damage_brush)),
                _Entry("Slow", f"{editor.slow_brush.percent} % langsamer"),
            ))
            if editing:
                entries.append(_Entry("Effektwerte öffnen", action=editor.open_effect_settings))
        elif editor.graphic_layer == "roof":
            visibility = editor.roof_visibility
            status = (f"{visibility.radius:g} Felder · {visibility.transparency} % · "
                      f"weicher Rand {visibility.softness:g}" if visibility.enabled else "Ausgeschaltet")
            entries.append(_Entry("Dach-Sichtfenster", status))
            if editing:
                entries.append(_Entry("Dachwerte öffnen", action=editor.open_roof_settings))
        if editing and (editor._move_anchor is not None or editor._selected_object() is not None):
            entries.append(_Entry("Objektgröße ändern", action=editor._open_object_size))
        return entries

    def _layers(self, editor, editing):
        mode = editor.placement_mode
        entries = []
        for layer, label in GRAPHIC_LAYERS.items():
            entries.append(_Entry(
                label,
                action=(lambda layer=layer: editor._set_graphic_layer(layer)) if editing else None,
                active=mode in ("graphics", "combined") and editor.graphic_layer == layer,
            ))
        entries.extend((
            _Entry("Kollisionen", action=(lambda: editor._set_placement_mode("collision")) if editing else None,
                   active=mode in ("collision", "combined")),
            _Entry("Effekte", action=(lambda: editor._set_placement_mode("damage")) if editing else None,
                   active=mode in ("damage", "slow")),
        ))
        if not editor.preview_active:
            entries.extend((
                _Entry(f"Kollisionsmarkierung · {'an' if editor.show_collisions else 'aus'}",
                       action=editor._toggle_collision_overlay, active=editor.show_collisions),
                _Entry(f"Effektmarkierung · {'an' if editor.show_effects else 'aus'}",
                       action=editor._toggle_effect_overlay, active=editor.show_effects),
            ))
        if editing:
            entries.append(_Entry(f"Dachansicht · {'an' if editor.show_roofs else 'aus'}",
                                  action=editor._toggle_roof_overlay, active=editor.show_roofs))
        return entries

    def _object_entry(self, editor, label, objects, cell):
        anchor = object_anchor_at(objects, cell)
        if anchor is None:
            return _Entry(label, "Leer")
        item = objects[anchor]
        x, y = anchor
        return _Entry(label, f"{_art_name(editor, item.asset_id)} · {item.width} × {item.height} · Anker {x} / {y}")

    def _cell(self, editor, editing):
        entries = []
        if editing:
            entries.append(_Entry("Zellen ansehen", action=editor.toggle_inspect_mode, active=editor.inspect_mode))
        cell = editor.inspected_cell
        if cell is None:
            return entries + [_Entry("Keine Zelle ausgewählt", "Wähle „Zellen ansehen“ und klicke auf die Karte.")]
        x, y = cell
        effects = editor.effects.get(cell)
        damage = effects.damage if effects else None
        slow = effects.slow if effects else None
        tile = editor.map[y][x]
        return entries + [
            _Entry(f"Zelle {x} / {y}"),
            self._object_entry(editor, "Dach", editor.roofs, cell),
            self._object_entry(editor, "Objekt", editor.objects, cell),
            _Entry("Kollision", editor.collisions.get(cell, "Leer")),
            _Entry("Schaden", _damage_detail(damage) if damage else "Leer"),
            _Entry("Slow", f"{slow.percent} % langsamer" if slow else "Leer"),
            _Entry("Boden", _art_name(editor, tile) if tile else "Leer"),
        ]

    def _entries(self, editor):
        editing = not editor.preview_active and editor.playtest is None
        if self.tab == "properties":
            return self._properties(editor, editing)
        if self.tab == "layers":
            return self._layers(editor, editing)
        if self.tab == "cell":
            return self._cell(editor, editing)
        if self.tab == "learn":
            entries = [
                _Entry("Dachbogen ausprobieren",
                       "Die mitgelieferte Karte zeigt, wie ein Dach und zwei Kollisionssäulen zusammenwirken."),
                _Entry("Durch den Bogen fahren",
                       "Starte den 1P- oder 2P-Test. Mit Standardbelegung fährt W für Spieler 1, ↑ für Spieler 2."),
            ]
            if editing:
                entries.append(_Entry("Dach-Demo öffnen", action=editor.load_roof_demo))
            return entries
        return [
            _Entry("Karte bewegen", "Mausrad zoomt. Ziehe mit der mittleren Maustaste oder Leertaste + Linksklick. "
                   "„Karte einpassen“ zeigt das ganze Spielfeld."),
            _Entry("Bearbeiten", "Linksklick platziert. Rechtsklick löscht auf der aktiven Ebene. Strg+Z macht rückgängig."),
            _Entry("Zellen ansehen", "Im Reiter „Zelle“ kannst du Daten prüfen, ohne die Karte zu bearbeiten."),
            _Entry("Test verlassen", "Esc oder F2 führt aus dem Leveltest in den Editor zurück."),
        ]

    def _wrap(self, text, width):
        lines = []
        line = ""
        for word in text.split():
            candidate = f"{line} {word}".lstrip()
            if line and self.font.size(candidate)[0] > width:
                lines.append(line)
                line = word
            else:
                line = candidate
            while self.font.size(line)[0] > width:
                end = len(line) - 1
                while end > 1 and self.font.size(line[:end])[0] > width:
                    end -= 1
                lines.append(line[:end])
                line = line[end:]
        if line:
            lines.append(line)
        return lines

    def _geometry(self, bounds, editor):
        gap = 5
        left = bounds.left + 9
        width = bounds.width - 18
        tab_width = (width - gap) // 2
        tabs = [(TABS[0][0], TABS[0][1], pygame.Rect(left, bounds.top + 34, width, 26))]
        tabs.extend(
            (key, label, pygame.Rect(left + column * (tab_width + gap), bounds.top + 64 + row * 30,
                                     tab_width, 26))
            for index, (key, label) in enumerate(TABS[1:]) for row, column in (divmod(index, 2),)
        )
        body = pygame.Rect(left, bounds.top + 129, width, max(0, bounds.height - 137))
        entries = []
        top = 0
        line_height = self.font.get_linesize()
        for entry in self._entries(editor):
            padding = 8 if entry.action else 0
            title = self._wrap(entry.title, width - 2 * padding - 2)
            detail = self._wrap(entry.detail, width - 2)
            height = max(28, len(title) * line_height + 10) if entry.action else (
                (len(title) + len(detail)) * line_height + 4
            )
            entries.append((entry, title, detail, pygame.Rect(left, top, width, height)))
            top += height + 6
        max_scroll = max(0, top - 6 - body.height)
        self._scroll = min(self._scroll, max_scroll)
        return tabs, body, entries, max_scroll

    def _text(self, screen, label, position, color=TEXT):
        screen.blit(self.font.render(label, True, color), position)

    def _draw_button(self, screen, rect, active):
        hovered = self._hover is not None and rect.collidepoint(self._hover)
        pygame.draw.rect(screen, ACTIVE if active else HOVER if hovered else BUTTON, rect, border_radius=5)
        pygame.draw.rect(screen, FOCUS if active or hovered else STROKE, rect, 1, border_radius=5)

    def draw(self, screen, bounds, editor):
        if bounds.width < 100 or bounds.height < 150:
            return
        old_clip = screen.get_clip()
        screen.set_clip(bounds.clip(old_clip))
        pygame.draw.rect(screen, PANEL, bounds, border_radius=7)
        pygame.draw.rect(screen, STROKE, bounds, 1, border_radius=7)
        self._text(screen, "Arbeitsbereich", (bounds.left + 10, bounds.top + 9), FOCUS)
        tabs, body, entries, max_scroll = self._geometry(bounds, editor)
        for key, label, rect in tabs:
            self._draw_button(screen, rect, self.tab == key)
            self._text(screen, label, (rect.x + 5, rect.centery - self.font.get_height() // 2))
        screen.set_clip(body.clip(old_clip))
        for entry, title, detail, local in entries:
            rect = local.move(0, body.top - self._scroll)
            if not rect.colliderect(body):
                continue
            if entry.action:
                self._draw_button(screen, rect, entry.active)
            x = rect.x + (8 if entry.action else 0)
            y = rect.y + (5 if entry.action else 0)
            for line in title:
                self._text(screen, line, (x, y), FOCUS if entry.active else TEXT)
                y += self.font.get_linesize()
            for line in detail:
                self._text(screen, line, (x, y), MUTED)
                y += self.font.get_linesize()
        if max_scroll:
            height = max(16, body.height * body.height // (body.height + max_scroll))
            y = body.top + (body.height - height) * self._scroll // max_scroll
            pygame.draw.line(screen, MUTED, (body.right - 2, y), (body.right - 2, y + height), 2)
        screen.set_clip(old_clip)

    def handle_event(self, event, bounds, editor):
        if event.type not in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL):
            return False
        position = getattr(event, "pos", pygame.mouse.get_pos())
        if event.type == pygame.MOUSEMOTION:
            self._hover = position if bounds.collidepoint(position) else None
            return False
        if bounds.width < 100 or bounds.height < 150 or not bounds.collidepoint(position):
            return False
        if event.type == pygame.MOUSEWHEEL:
            max_scroll = self._geometry(bounds, editor)[3]
            self._scroll = max(0, min(max_scroll, self._scroll - event.y * 48))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            tabs, body, entries, _ = self._geometry(bounds, editor)
            for key, _, rect in tabs:
                if rect.collidepoint(position):
                    self.show(key)
                    return True
            if body.collidepoint(position):
                local_pos = (position[0], position[1] - body.top + self._scroll)
                for entry, _, _, rect in entries:
                    if entry.action and rect.collidepoint(local_pos):
                        entry.action()
                        break
        return True

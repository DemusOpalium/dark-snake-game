"""The World Studio workspace for properties, layers, and map inspection."""

from collections.abc import Callable
from dataclasses import dataclass

import pygame

from modules.editor_buttons import EditorButtons
from modules.editor_layers import LAYER_COLORS, LAYER_LABELS
from modules.graphic_objects import object_anchor_at


PANEL = (24, 33, 48)
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
GRAPHIC_LAYERS = frozenset(("ground", "objects", "roof"))


@dataclass(frozen=True, slots=True)
class _Control:
    action_id: str
    label: str
    action: Callable[[], None]
    hint: str
    active: bool = False
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class _Entry:
    title: str
    detail: str = ""
    action: Callable[[], None] | None = None
    active: bool = False
    action_id: str | None = None
    controls: tuple[_Control, ...] = ()
    accent: tuple[int, int, int] | None = None


def _tool_name(editor):
    if editor.inspect_mode:
        return "Zellen ansehen"
    if editor.eraser_active:
        return "Radierer"
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

    def __init__(self, font, button_art=None):
        self.font = font
        self.button_art = button_art if button_art is not None else EditorButtons(font)
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
        layer = LAYER_LABELS[editor.active_layer]
        entries = [_Entry("Aktives Werkzeug", f"{_tool_name(editor)} · {layer}")]
        if editing and editor.layer_locked(editor.active_layer):
            entries.append(_Entry("Bearbeitung gesperrt", "Die aktive Ebene im Layer Explorer entsperren."))
        elif editing and not editor.layer_visible(editor.active_layer):
            entries.append(_Entry("Ebene ausgeblendet", "Die aktive Ebene im Layer Explorer einblenden."))
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
                entries.append(_Entry("Effektwerte öffnen", action=editor.open_effect_settings,
                                      action_id="effect_values"))
        elif editor.graphic_layer == "roof":
            visibility = editor.roof_visibility
            status = (f"{visibility.radius:g} Felder · {visibility.transparency} % · "
                      f"weicher Rand {visibility.softness:g}" if visibility.enabled else "Ausgeschaltet")
            entries.append(_Entry("Dach-Sichtfenster", status))
            if editing:
                entries.append(_Entry("Dachwerte öffnen", action=editor.open_roof_settings,
                                      action_id="roof_settings"))
        if editing and (editor._move_anchor is not None or editor._selected_object() is not None):
            entries.append(_Entry("Objektgröße ändern", action=editor._open_object_size,
                                  action_id="build_object_size"))
        return entries

    def _layers(self, editor, editing):
        entries = []
        if editing:
            if editor.solo_layer is not None:
                layer = editor.solo_layer
                entries.append(_Entry(
                    "Solo · " + LAYER_LABELS[layer],
                    controls=(_Control("layer_exit_solo", "Solo beenden",
                                       lambda layer=layer: editor.toggle_layer_solo(layer),
                                       "Die vorherige Sichtbarkeit wiederherstellen."),),
                ))
            entries.append(_Entry(
                "Ebenenansicht", "Sicht · Schutz · Solo",
                controls=(
                    _Control("layer_show_all", "Alle Ebenen anzeigen", editor.show_all_layers,
                             "Alle fünf Ebenen einblenden."),
                ),
            ))
        for layer, label in LAYER_LABELS.items():
            visible = editor.layer_visible(layer)
            locked = editor.layer_locked(layer)
            active = editor.active_layer == layer
            if not editing:
                entries.append(_Entry(label, accent=LAYER_COLORS[layer]))
                continue
            entries.append(_Entry(
                label, active=active, accent=LAYER_COLORS[layer],
                action=lambda layer=layer: self._choose_layer(editor, layer),
                action_id=f"layer_{layer}",
                controls=(
                    _Control(f"layer_visibility_{layer}", "An" if visible else "Aus",
                             lambda layer=layer: editor.toggle_layer_visibility(layer),
                             f"{label} ein- oder ausblenden.", visible, editor.solo_layer is None),
                    _Control(f"layer_lock_{layer}", "Zu" if locked else "Offen",
                             lambda layer=layer: editor.toggle_layer_lock(layer),
                             f"Bearbeitungsschutz für {label} umschalten.", locked),
                    _Control(f"layer_solo_{layer}", "Solo", lambda layer=layer: editor.toggle_layer_solo(layer),
                             f"{label} vorübergehend allein anzeigen.", editor.solo_layer == layer),
                ),
            ))
        return entries

    @staticmethod
    def _choose_layer(editor, layer):
        if layer in GRAPHIC_LAYERS:
            editor._set_graphic_layer(layer)
        else:
            editor._set_placement_mode("damage" if layer == "effects" else "collision")

    @staticmethod
    def _deletion_control(editor, layer, effect=None):
        name = {"damage": "Schaden", "slow": "Slow"}.get(effect, LAYER_LABELS[layer])
        return _Control(
            f"inspector_delete_{effect or layer}", "Löschen", lambda: editor.delete_inspected(layer, effect),
            f"{name} nach Bestätigung aus der ausgewählten Zelle entfernen.",
            enabled=editor.layer_editable(layer),
        )

    def _object_entry(self, editor, layer, label, objects, cell, editing):
        anchor = object_anchor_at(objects, cell)
        if anchor is None:
            return _Entry(label, "Leer", accent=LAYER_COLORS[layer])
        item = objects[anchor]
        x, y = anchor
        controls = ()
        if editing:
            controls = (
                _Control(f"inspector_select_{layer}", "Auswählen", lambda: editor.select_inspected_object(layer),
                         f"{label} zum Verschieben oder Ändern der Größe auswählen.",
                         enabled=editor.layer_editable(layer)),
                self._deletion_control(editor, layer),
            )
        detail = f"{_art_name(editor, item.asset_id)} · {item.width} × {item.height} · Anker {x} / {y}"
        return _Entry(label, detail, controls=controls, accent=LAYER_COLORS[layer])

    def _effect_entry(self, editor, kind, label, detail, editing):
        controls = ()
        if editing and detail is not None:
            controls = (
                _Control(f"inspector_edit_{kind}", "Bearbeiten", lambda: editor.edit_inspected_effect(kind),
                         f"{label} für diese Zelle einstellen.", enabled=editor.layer_editable("effects")),
                self._deletion_control(editor, "effects", kind),
            )
        return _Entry(label, detail or "Leer", controls=controls, accent=LAYER_COLORS["effects"])

    def _cell(self, editor, editing):
        entries = []
        if editing:
            entries.append(_Entry("Zelle auf Karte wählen", action=editor.toggle_inspect_mode,
                                  active=editor.inspect_mode, action_id="inspector_pick_cell"))
        cell = editor.inspected_cell
        if cell is None:
            return entries + [_Entry("Keine Zelle ausgewählt", "Aktiviere die Auswahl und klicke auf die Karte.")]
        x, y = cell
        effects = editor.effects.get(cell)
        damage = effects.damage if effects else None
        slow = effects.slow if effects else None
        tile = editor.map[y][x]
        collision = editor.collisions.get(cell)
        collision_controls = ()
        ground_controls = ()
        if editing and collision is not None:
            kind = "BARRIER" if collision == "WALL" else "WALL"
            collision_controls = (
                _Control(f"inspector_collision_{kind.lower()}", f"Zu {kind}",
                         lambda: editor.edit_inspected_collision(kind),
                         f"Kollision in dieser Zelle als {kind} speichern.",
                         enabled=editor.layer_editable("collision")),
                self._deletion_control(editor, "collision"),
            )
        if editing and tile is not None:
            ground_controls = (self._deletion_control(editor, "ground"),)
        return entries + [
            _Entry(f"Zelle {x} / {y}"),
            self._object_entry(editor, "roof", "Dach", editor.roofs, cell, editing),
            self._object_entry(editor, "objects", "Objekt", editor.objects, cell, editing),
            _Entry("Kollision", collision or "Leer", controls=collision_controls, accent=LAYER_COLORS["collision"]),
            self._effect_entry(editor, "damage", "Schaden", _damage_detail(damage) if damage else None, editing),
            self._effect_entry(editor, "slow", "Slow", f"{slow.percent} % langsamer" if slow else None, editing),
            _Entry("Boden", _art_name(editor, tile) if tile else "Leer",
                   controls=ground_controls, accent=LAYER_COLORS["ground"]),
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
                entries.append(_Entry("Dach-Demo öffnen", action=editor.load_roof_demo,
                                      action_id="test_roof_demo"))
            return entries
        return [
            _Entry("Karte bewegen", "Mausrad zoomt. Ziehe mit der mittleren Maustaste oder Leertaste + Linksklick. "
                   "„Karte einpassen“ zeigt das ganze Spielfeld."),
            _Entry("Bearbeiten", "Linksklick platziert. Rechtsklick fragt vor dem Löschen nach. "
                   "Unter Bauen schaltet der Radierer direktes Löschen ein. Strg+Z macht rückgängig."),
            _Entry("Layer Explorer", "Verdeckte oder gesperrte Ebenen schützen vor Änderungen. Solo zeigt nur eine Ebene."),
            _Entry("Zellen ansehen", "Im Reiter „Zelle“ kannst du Daten prüfen und einzelne Werte bearbeiten."),
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
        tabs = [(TABS[0][0], TABS[0][1], pygame.Rect(left, bounds.top + 31, width, 34))]
        tabs.extend(
            (key, label, pygame.Rect(left + column * (tab_width + gap), bounds.top + 69 + row * 33,
                                     tab_width, 29))
            for index, (key, label) in enumerate(TABS[1:]) for row, column in (divmod(index, 2),)
        )
        body = pygame.Rect(left, bounds.top + 139, width - 6, max(0, bounds.height - 147))
        entries = []
        top = 0
        line_height = self.font.get_linesize()
        for entry in self._entries(editor):
            text_width = body.width - (8 if entry.accent else 2)
            title = self._wrap(entry.title, text_width) if entry.action is None else []
            detail = self._wrap(entry.detail, text_width)
            height = (34 if entry.action else len(title) * line_height) + len(detail) * line_height
            if entry.controls:
                height += 32
            entries.append((entry, title, detail, pygame.Rect(left, top, body.width, height)))
            top += height + 8
        max_scroll = max(0, top - 8 - body.height)
        self._scroll = min(self._scroll, max_scroll)
        return tabs, body, entries, max_scroll

    def _text(self, screen, label, position, color=TEXT):
        screen.blit(self.font.render(label, True, color), position)

    def _entry_targets(self, entry, rect):
        offset = 6 if entry.accent else 0
        left, width = rect.x + offset, rect.width - offset
        if entry.action:
            yield (_Control(entry.action_id, entry.title, entry.action,
                            self.button_art.hint(entry.action_id, entry.title), entry.active),
                   pygame.Rect(left, rect.top, width, 34))
        if entry.controls:
            count = len(entry.controls)
            available = width - (count - 1) * 3
            widths = [max(40, self.font.size(control.label)[0] + 12) for control in entry.controls]
            preferred = sum(widths)
            for control, minimum in zip(entry.controls, widths, strict=True):
                control_width = (minimum + (available - preferred) // count if preferred <= available
                                 else available * minimum // preferred)
                yield control, pygame.Rect(left, rect.bottom - 27, control_width, 27)
                left += control_width + 3

    def _hovered(self, rect):
        return self._hover is not None and rect.collidepoint(self._hover)

    def _draw_entry(self, screen, body, entry, rect, title, detail):
        if entry.accent:
            pygame.draw.rect(screen, entry.accent, (rect.x, rect.y + 2, 3, rect.height - 4), border_radius=2)
        hint = None
        for control, target in self._entry_targets(entry, rect):
            hovered = self._hovered(target.clip(body))
            self.button_art.draw(screen, control.action_id, control.label, target,
                                 active=control.active, hovered=hovered, enabled=control.enabled)
            if hovered:
                hint = control.hint
                if not control.enabled:
                    hint += " Derzeit nicht verfügbar."
        x = rect.x + (6 if entry.accent else 0)
        y = rect.y + (34 if entry.action else 0)
        for lines, color in ((title, TEXT), (detail, MUTED)):
            for line in lines:
                self._text(screen, line, (x, y), color)
                y += self.font.get_linesize()
        return hint

    def draw(self, screen, bounds, editor):
        if bounds.width < 100 or bounds.height < 150:
            return
        old_clip = screen.get_clip()
        screen.set_clip(bounds.clip(old_clip))
        pygame.draw.rect(screen, PANEL, bounds, border_radius=7)
        pygame.draw.rect(screen, STROKE, bounds, 1, border_radius=7)
        self._text(screen, "Arbeitsbereich", (bounds.left + 10, bounds.top + 9), FOCUS)
        tabs, body, entries, max_scroll = self._geometry(bounds, editor)
        hint = None
        for key, label, rect in tabs:
            action_id = f"sidebar_{key}"
            hovered = self._hovered(rect)
            self.button_art.draw(screen, action_id, label, rect, selected=self.tab == key, hovered=hovered)
            if hovered:
                hint = self.button_art.hint(action_id, label)
        screen.set_clip(body.clip(old_clip))
        for entry, title, detail, local in entries:
            rect = local.move(0, body.top - self._scroll)
            if not rect.colliderect(body):
                continue
            hint = self._draw_entry(screen, body, entry, rect, title, detail) or hint
        screen.set_clip(bounds.clip(old_clip))
        if max_scroll:
            height = min(body.height, max(16, body.height * body.height // (body.height + max_scroll)))
            y = body.top + (body.height - height) * self._scroll // max_scroll
            pygame.draw.line(screen, MUTED, (body.right + 3, y), (body.right + 3, y + height), 2)
        screen.set_clip(old_clip)
        if hint:
            self._draw_hint(screen, bounds, body, hint)

    def _draw_hint(self, screen, bounds, body, hint):
        lines = self._wrap(hint, body.width - 16)[:4]
        height = self.font.get_linesize()
        box = pygame.Rect(body.x, 0, body.width, len(lines) * height + 12)
        box.bottom = min(bounds.bottom - 6, self._hover[1] + box.height + 20)
        if box.collidepoint(self._hover):
            box.bottom = self._hover[1] - 6
        box.top = max(bounds.top + 6, box.top)
        pygame.draw.rect(screen, PANEL, box, border_radius=5)
        pygame.draw.rect(screen, FOCUS, box, 1, border_radius=5)
        for index, line in enumerate(lines):
            self._text(screen, line, (box.x + 8, box.y + 6 + height * index))

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
                    for control, target in self._entry_targets(entry, rect):
                        if target.collidepoint(local_pos):
                            if control.enabled:
                                control.action()
                            return True
        return True

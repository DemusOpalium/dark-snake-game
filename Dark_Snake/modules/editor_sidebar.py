"""The World Studio workspace for properties, layers, and map inspection."""

from collections.abc import Callable
from dataclasses import dataclass

import pygame

from modules.editor_buttons import EditorButtons
from modules.editor_layers import LAYER_COLORS, LAYER_LABELS
from modules.graphic_objects import object_anchor_at
from modules.studio_locale import StudioLocale
from modules.studio_tutorial_text import TUTORIAL_STEPS, TUTORIAL_TITLE


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
LEARN_NAVIGATION = frozenset(("learn_start", "learn_previous", "learn_next", "learn_retry", "learn_exit"))


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


def _damage_detail(damage, tr):
    def seconds(value):
        return format(value, "g").replace(".", tr(",")) + " s"

    duration = (tr("Keine Zeitgrenze") if damage.duration is None
                else tr("Dauer {duration}", duration=seconds(damage.duration)))
    return tr("{amount} HP je {interval} · {duration}", amount=damage.amount,
              interval=seconds(damage.interval), duration=duration)


def _art_name(editor, key):
    asset = editor.frost_assets.get(key)
    return asset.name if asset is not None else key


class StudioSidebar:
    """Present the existing editor tools in one switchable right-hand pane."""

    def __init__(self, font, button_art=None, *, translate=None):
        self.font = font
        self.button_art = button_art if button_art is not None else EditorButtons(font)
        self.tr = translate if translate is not None else StudioLocale("de")
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
        layer = self.tr(LAYER_LABELS[editor.active_layer])
        entries = [_Entry(self.tr("Aktives Werkzeug"), f"{self.tr(_tool_name(editor))} · {layer}")]
        if editing and editor.layer_locked(editor.active_layer):
            entries.append(_Entry(self.tr("Bearbeitung gesperrt"),
                                  self.tr("Die aktive Ebene im Layer Explorer entsperren.")))
        elif editing and not editor.layer_visible(editor.active_layer):
            entries.append(_Entry(self.tr("Ebene ausgeblendet"),
                                  self.tr("Die aktive Ebene im Layer Explorer einblenden.")))
        item = editor._selected_object()
        has_tile = editor.graphic_layer == "ground" and editor._has_ground_art(editor.current_tile)
        if mode in ("graphics", "combined") and (has_tile or item is not None):
            size = f" · {item.width} × {item.height}" if item is not None else ""
            entries.append(_Entry(self.tr("Gewählte Grafik"), f"{_art_name(editor, editor.current_tile)}{size}"))
        if mode in ("damage", "slow"):
            entries.extend((
                _Entry(self.tr("Schaden"), _damage_detail(editor.damage_brush, self.tr)),
                _Entry(self.tr("Slow"), self.tr("{percent} % langsamer", percent=editor.slow_brush.percent)),
            ))
            if editing:
                entries.append(_Entry(self.tr("Effektwerte öffnen"), action=editor.open_effect_settings,
                                      action_id="effect_values"))
        elif editor.graphic_layer == "roof":
            visibility = editor.roof_visibility
            status = (self.tr("{radius:g} Felder · {alpha} % · weicher Rand {softness:g}",
                              radius=visibility.radius, alpha=visibility.transparency, softness=visibility.softness)
                      if visibility.enabled else self.tr("Ausgeschaltet"))
            entries.append(_Entry(self.tr("Dach-Sichtfenster"), status))
            if editing:
                entries.append(_Entry(self.tr("Dachwerte öffnen"), action=editor.open_roof_settings,
                                      action_id="roof_settings"))
        if editing and (editor._move_anchor is not None or editor._selected_object() is not None):
            entries.append(_Entry(self.tr("Objektgröße ändern"), action=editor._open_object_size,
                                  action_id="build_object_size"))
        return entries

    def _layers(self, editor, editing):
        entries = []
        if editing:
            if editor.solo_layer is not None:
                layer = editor.solo_layer
                entries.append(_Entry(
                    "Solo · " + self.tr(LAYER_LABELS[layer]),
                    controls=(_Control("layer_exit_solo", self.tr("Solo beenden"),
                                       lambda layer=layer: editor.toggle_layer_solo(layer),
                                       self.tr("Die vorherige Sichtbarkeit wiederherstellen.")),),
                ))
            entries.append(_Entry(
                self.tr("Ebenenansicht"), self.tr("Sicht · Schutz · Solo"),
                controls=(
                    _Control("layer_show_all", self.tr("Alle Ebenen anzeigen"), editor.show_all_layers,
                             self.tr("Alle fünf Ebenen einblenden.")),
                ),
            ))
        for layer, label in LAYER_LABELS.items():
            label = self.tr(label)
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
                    _Control(f"layer_visibility_{layer}", self.tr("An" if visible else "Aus"),
                             lambda layer=layer: editor.toggle_layer_visibility(layer),
                             self.tr("{layer} ein- oder ausblenden.", layer=label), visible, editor.solo_layer is None),
                    _Control(f"layer_lock_{layer}", self.tr("Zu" if locked else "Offen"),
                             lambda layer=layer: editor.toggle_layer_lock(layer),
                             self.tr("Bearbeitungsschutz für {layer} umschalten.", layer=label), locked),
                    _Control(f"layer_solo_{layer}", "Solo", lambda layer=layer: editor.toggle_layer_solo(layer),
                             self.tr("{layer} vorübergehend allein anzeigen.", layer=label),
                             editor.solo_layer == layer),
                ),
            ))
        return entries

    @staticmethod
    def _choose_layer(editor, layer):
        if layer in GRAPHIC_LAYERS:
            editor._set_graphic_layer(layer)
        else:
            editor._set_placement_mode("damage" if layer == "effects" else "collision")

    def _deletion_control(self, editor, layer, effect=None):
        name = self.tr({"damage": "Schaden", "slow": "Slow"}.get(effect, LAYER_LABELS[layer]))
        return _Control(
            f"inspector_delete_{effect or layer}", self.tr("Löschen"), lambda: editor.delete_inspected(layer, effect),
            self.tr("{name} nach Bestätigung aus der ausgewählten Zelle entfernen.", name=name),
            enabled=editor.layer_editable(layer),
        )

    def _object_entry(self, editor, layer, label, objects, cell, editing):
        anchor = object_anchor_at(objects, cell)
        if anchor is None:
            return _Entry(label, self.tr("Leer"), accent=LAYER_COLORS[layer])
        item = objects[anchor]
        x, y = anchor
        controls = ()
        if editing:
            controls = (
                _Control(f"inspector_select_{layer}", self.tr("Auswählen"),
                         lambda: editor.select_inspected_object(layer),
                         self.tr("{label} zum Verschieben oder Ändern der Größe auswählen.", label=label),
                         enabled=editor.layer_editable(layer)),
                self._deletion_control(editor, layer),
            )
        detail = self.tr("{asset} · {width} × {height} · Anker {x} / {y}", asset=_art_name(editor, item.asset_id),
                         width=item.width, height=item.height, x=x, y=y)
        return _Entry(label, detail, controls=controls, accent=LAYER_COLORS[layer])

    def _effect_entry(self, editor, kind, label, detail, editing):
        controls = ()
        if editing and detail is not None:
            controls = (
                _Control(f"inspector_edit_{kind}", self.tr("Bearbeiten"), lambda: editor.edit_inspected_effect(kind),
                         self.tr("{label} für diese Zelle einstellen.", label=label),
                         enabled=editor.layer_editable("effects")),
                self._deletion_control(editor, "effects", kind),
            )
        return _Entry(label, detail or self.tr("Leer"), controls=controls, accent=LAYER_COLORS["effects"])

    def _cell(self, editor, editing):
        entries = []
        if editing:
            entries.append(_Entry(self.tr("Zelle auf Karte wählen"), action=editor.toggle_inspect_mode,
                                  active=editor.inspect_mode, action_id="inspector_pick_cell"))
        cell = editor.inspected_cell
        if cell is None:
            return entries + [_Entry(self.tr("Keine Zelle ausgewählt"),
                                     self.tr("Aktiviere die Auswahl und klicke auf die Karte."))]
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
                _Control(f"inspector_collision_{kind.lower()}", self.tr("Zu {kind}", kind=kind),
                         lambda: editor.edit_inspected_collision(kind),
                         self.tr("Kollision in dieser Zelle als {kind} speichern.", kind=self.tr(kind)),
                         enabled=editor.layer_editable("collision")),
                self._deletion_control(editor, "collision"),
            )
        if editing and tile is not None:
            ground_controls = (self._deletion_control(editor, "ground"),)
        return entries + [
            _Entry(self.tr("Zelle {x} / {y}", x=x, y=y)),
            self._object_entry(editor, "roof", self.tr("Dach"), editor.roofs, cell, editing),
            self._object_entry(editor, "objects", self.tr("Objekt"), editor.objects, cell, editing),
            _Entry(self.tr("Kollision"), self.tr(collision or "Leer"),
                   controls=collision_controls, accent=LAYER_COLORS["collision"]),
            self._effect_entry(editor, "damage", self.tr("Schaden"),
                               _damage_detail(damage, self.tr) if damage else None, editing),
            self._effect_entry(editor, "slow", self.tr("Slow"),
                               self.tr("{percent} % langsamer", percent=slow.percent) if slow else None, editing),
            _Entry(self.tr("Boden"), _art_name(editor, tile) if tile else self.tr("Leer"),
                   controls=ground_controls, accent=LAYER_COLORS["ground"]),
        ]

    def _learning(self, editor, editing):
        if editor.tutorial is not None:
            return self._tutorial(editor, editing)
        entries = [
            _Entry(self.tr(TUTORIAL_TITLE),
                   self.tr("Baue eine Übungskarte in fünf Schritten. Dein aktueller Entwurf bleibt erhalten.")),
        ]
        if editing:
            entries.append(_Entry(self.tr("Übung starten"), action=editor.start_tutorial, action_id="learn_start"))
        entries.extend((
            _Entry(self.tr("Dachbogen ausprobieren"),
                   self.tr("Öffne die Dach-Demo und schalte im Layer Explorer Dach und Kollision einzeln um. "
                           "So siehst du den freien Durchgang zwischen den Säulen.")),
            _Entry(self.tr("Durch den Bogen fahren"),
                   self.tr("Starte Test (1P) oder Test (2P). Mit der Standardbelegung lenkt W Spieler 1 "
                           "und ↑ Spieler 2 durch den Bogen. Esc oder F2 beendet den Test.")),
        ))
        if editing:
            entries.append(_Entry(self.tr("Dach-Demo öffnen"), action=editor.load_roof_demo,
                                  action_id="test_roof_demo"))
        return entries

    def _tutorial_control(self, action_id, label, action, *, hint=None, enabled=True, active=False):
        return _Control(action_id, self.tr(label), action,
                        self.tr(hint or self.button_art.hint(action_id, label)), active, enabled)

    def _tutorial(self, editor, editing):
        progress = editor.tutorial_progress()
        index = editor.tutorial.step_index
        last_step = index == len(TUTORIAL_STEPS) - 1
        previous_complete = all(progress[:index])
        complete = previous_complete and progress[index]
        title, task, example = (self.tr(source) for source, _ in TUTORIAL_STEPS[index])
        entries = [
            _Entry(title,
                   self.tr("Schritt {step}/{total} · {checked} geprüft",
                           step=index + 1, total=len(TUTORIAL_STEPS), checked=sum(progress)),
                   accent=FOCUS if complete else None),
        ]
        if not editing:
            if editor.playtest is not None:
                entries.append(_Entry(self.tr("Test läuft"),
                                      self.tr("Esc oder F2 beendet den Test und zeigt deinen Fortschritt.")))
            else:
                entries.append(_Entry(self.tr("Beende die Vorschau, um mit der Übung fortzufahren.")))
            return entries

        control = self._tutorial_control
        leave = _Entry(self.tr("Zurück zum Editor"), action=editor.leave_tutorial, action_id="learn_exit")
        show_example = editor.tutorial.example_visible
        finished = last_step and complete
        if finished:
            entries.extend((_Entry(self.tr("Glückwunsch! Dein erstes FrostAge-Level ist fertig.")), leave))
        else:
            entries.append(_Entry(self.tr("Beispiel") if show_example else "", example if show_example else task))
        if last_step:
            entries.append(_Entry("", controls=(
                control("test_player_1", "Test (1P)", lambda: editor.start_playtest(1),
                        hint="Starte den 1P-Test für diesen Schritt.", enabled=previous_complete),
                control("test_player_2", "Test (2P)", lambda: editor.start_playtest(2),
                        hint="Probiere die Übungskarte zu zweit aus.", enabled=complete),
            )))
        entries.extend((
            _Entry("", controls=(
                control("learn_previous", "Zurück", editor.tutorial_previous, enabled=index > 0),
                control("learn_next", "Weiter", editor.tutorial_next, enabled=complete and not last_step,
                        hint="Schließe diesen und die vorherigen Schritte ab." if not complete else None),
            )),
            _Entry("", controls=(
                control("learn_retry", "Wiederholen", editor.tutorial_retry),
                control("learn_example", "Beispiel", editor.tutorial_toggle_example,
                        active=editor.tutorial.example_visible),
            )),
        ))
        if finished and show_example:
            entries.append(_Entry(self.tr("Beispiel"), example))
        if not previous_complete:
            entries.append(_Entry(self.tr("Öffne zuerst die vorherigen Schritte und prüfe ihre Aufgaben.")))
        if not finished:
            entries.append(leave)
        return entries

    def _entries(self, editor):
        editing = not editor.preview_active and editor.playtest is None
        if self.tab == "properties":
            return self._properties(editor, editing)
        if self.tab == "layers":
            return self._layers(editor, editing)
        if self.tab == "cell":
            return self._cell(editor, editing)
        if self.tab == "learn":
            return self._learning(editor, editing)
        return [
            _Entry(self.tr("Layer Explorer"),
                   self.tr("Wähle die aktive Ebene zum Malen. Sichtbarkeit und Sperre funktionieren unabhängig. "
                           "Solo blendet die übrigen Ebenen vorübergehend aus.")),
            _Entry(self.tr("Kollision"),
                   self.tr("Wand oder Barriere markieren blockierte Felder unabhängig von der Grafik. "
                           "Mit „Grafik + Kollision“ malst du beides zusammen.")),
            _Entry(self.tr("Dach / Foreground"),
                   self.tr("Dächer werden vor den Spielfiguren gezeichnet. Stelle unter „Dachwerte“ "
                           "das transparente Sichtfenster pro Spieler ein.")),
            _Entry(self.tr("Malen und Löschen"),
                   self.tr("Mit gedrückter linker Maustaste malst du Kacheln. Rechtsklick oder Rechtsziehen "
                           "löscht sofort auf sichtbaren, ungesperrten Ebenen. Unter Bauen kannst du das "
                           "auf die aktive Ebene einschränken. Strg+Z und Strg+Y machen einen Zug rückgängig "
                           "oder wiederholen ihn.")),
            _Entry(self.tr("Zellen ansehen"),
                   self.tr("Im Reiter „Zelle“ kannst du Daten prüfen und einzelne Werte bearbeiten.")),
            _Entry(self.tr("Speichern und öffnen"),
                   self.tr("Öffne „Datei“, um einen Entwurf zu speichern, umzubenennen oder erneut zu laden.")),
            _Entry(self.tr("Level testen"),
                   self.tr("„Test (1P)“ und „Test (2P)“ prüfen Wege und Effekte im Entwurf. "
                           "Esc oder F2 führt in den Editor zurück.")),
            _Entry(self.tr("Karte bewegen"),
                   self.tr("Mausrad zoomt. Ziehe mit der mittleren Maustaste oder Leertaste + Linksklick. "
                           "„Karte einpassen“ zeigt das ganze Spielfeld.")),
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
        tabs = [(TABS[0][0], self.tr(TABS[0][1]), pygame.Rect(left, bounds.top + 31, width, 34))]
        tabs.extend(
            (key, self.tr(label), pygame.Rect(left + column * (tab_width + gap), bounds.top + 69 + row * 33,
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
                            self.tr(self.button_art.hint(entry.action_id, entry.title)), entry.active),
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
                    hint += " " + self.tr("Derzeit nicht verfügbar.")
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
        self._text(screen, self.tr("Arbeitsbereich"), (bounds.left + 10, bounds.top + 9), FOCUS)
        tabs, body, entries, max_scroll = self._geometry(bounds, editor)
        hint = None
        for key, label, rect in tabs:
            action_id = f"sidebar_{key}"
            hovered = self._hovered(rect)
            self.button_art.draw(screen, action_id, label, rect, selected=self.tab == key, hovered=hovered)
            if hovered:
                hint = self.tr(self.button_art.hint(action_id, label))
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
                                if control.action_id in LEARN_NAVIGATION:
                                    self._scroll = 0
                            return True
        return True

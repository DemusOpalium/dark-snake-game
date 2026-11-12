"""World Studio browser for saved drafts and the planned game order."""

import pygame

from modules.world_library import WorldLibrary


ROW_HEIGHT = 28
FREE_LABEL = "Freie Level"
BG = (26, 24, 31)
PANEL = (37, 34, 45)
BUTTON = (70, 51, 88)
SELECTED = (112, 76, 122)
TEXT = (244, 239, 248)
MUTED = (194, 186, 205)
ACCENT = (246, 199, 105)


class WorldTree:
    def __init__(self, bounds, font, open_draft, ask_name, close):
        self.font = font
        self.open_draft = open_draft
        self.ask_name = ask_name
        self.close = close
        self.panel = pygame.Rect(0, 0, min(bounds.width - 32, 1050), min(bounds.height - 42, 720))
        self.panel.center = bounds.center
        column_width = (self.panel.width - 58) // 2
        top = self.panel.y + 96
        height = (self.panel.bottom - 123 - top) // ROW_HEIGHT * ROW_HEIGHT
        self.design = pygame.Rect(self.panel.x + 18, top, column_width, height)
        self.order = self.design.move(column_width + 22, 0)
        self.library = None
        self.selected_level = None
        self.target_world = None
        self.expanded = {None}
        self.design_offset = self.order_offset = 0
        self.dragged_level = None
        self.message = ""

    def open(self, current_draft):
        self.library = WorldLibrary.load()
        if self.selected_level not in self.library.levels:
            self.selected_level = None
        if self.target_world not in self.library.worlds:
            self.target_world = None
        if current_draft:
            current = self.library.level_for_draft(current_draft)
            if current:
                self.selected_level = current.id
                self.target_world = current.world_id
                self.expanded.add(current.world_id)
        self.dragged_level = None
        self.message = ""

    def _design_rows(self):
        grouped = {world_id: [] for world_id in [None, *self.library.worlds]}
        for level in sorted(self.library.levels.values(), key=lambda entry: entry.name.casefold()):
            grouped[level.world_id].append(level)
        worlds = sorted(self.library.worlds.values(), key=lambda world: world.name.casefold())
        for world_id, label in [(None, FREE_LABEL), *((world.id, world.name) for world in worlds)]:
            yield "world", world_id, label
            if world_id in self.expanded:
                for level in grouped[world_id]:
                    name = level.name
                    if name != level.draft_name:
                        name = f"{name} · {level.draft_name}.json"
                    yield "level", level.id, name

    def _rows(self, area):
        if area == self.design:
            rows = list(self._design_rows())
            offset_name = "design_offset"
        else:
            rows = [("level", level_id, f"{index}. {self.library.levels[level_id].name}")
                    for index, level_id in enumerate(self.library.game_order, 1)]
            offset_name = "order_offset"
        capacity = area.height // ROW_HEIGHT
        offset = max(0, min(getattr(self, offset_name), len(rows) - capacity))
        setattr(self, offset_name, offset)
        for index, (kind, item_id, label) in enumerate(rows[offset:offset + capacity]):
            rect = pygame.Rect(area.x, area.y + index * ROW_HEIGHT, area.width, ROW_HEIGHT - 2)
            yield rect, kind, item_id, label

    def _controls(self):
        buttons = (
            (self.design, 0, (("Welt neu", self._new_world), ("Welt umbenennen", self._rename_world))),
            (self.design, 1, (("Level umbenennen", self._rename_level), ("Zuordnen", self._assign))),
            (self.order, 0, (("Zur Reihenfolge", self._add), ("Entfernen", self._remove))),
            (self.order, 1, (("Nach oben", lambda: self._move(-1)), ("Nach unten", lambda: self._move(1)))),
        )
        for area, row, controls in buttons:
            width = (area.width - 8) // 2
            for column, (label, action) in enumerate(controls):
                yield pygame.Rect(area.x + column * (width + 8), area.bottom + 9 + 33 * row, width, 28), label, action
        yield pygame.Rect(self.panel.right - 123, self.panel.bottom - 38, 105, 27), "Schließen", self.close

    def _write(self, action, *args, success):
        try:
            result = action(*args)
        except (OSError, ValueError) as error:
            self.message = str(error)
            return None
        self.message = success
        return result

    def _new_world(self):
        def create(name):
            world_id = self._write(self.library.create_world, name, success="Welt angelegt")
            if world_id is not None:
                self.target_world = world_id
                self.expanded.add(world_id)

        self.ask_name("Neue Themenwelt", "", create)

    def _rename_world(self):
        world = self.library.worlds.get(self.target_world)
        if world is None:
            self.message = "Eine Themenwelt anklicken."
            return
        self.ask_name("Themenwelt umbenennen", world.name,
                      lambda name: self._write(self.library.rename_world, world.id, name, success="Welt umbenannt"))

    def _level(self):
        level = self.library.levels.get(self.selected_level)
        if level is None:
            self.message = "Ein Level in der Bibliothek oder der Reihenfolge auswählen."
        return level

    def _rename_level(self):
        level = self._level()
        if level:
            self.ask_name("Level umbenennen", level.name,
                          lambda name: self._write(self.library.rename_level, level.id, name, success="Level umbenannt"))

    def _assign(self):
        level = self._level()
        if level:
            self._write(self.library.assign_level, level.id, self.target_world, success="Zuordnung gespeichert")
            self.expanded.add(self.target_world)

    def _add(self):
        level = self._level()
        if level:
            if level.id in self.library.game_order:
                self.message = "Dieses Level steht bereits in der Reihenfolge."
            else:
                self._write(self.library.add_to_game_order, level.id, success="Reihenfolge gespeichert")

    def _ordered_level(self):
        level = self._level()
        if level and level.id not in self.library.game_order:
            self.message = "Dieses Level steht nicht in der Reihenfolge."
            return None
        return level

    def _remove(self):
        if level := self._ordered_level():
            self._write(self.library.remove_from_game_order, level.id, success="Reihenfolge gespeichert")

    def _move(self, offset):
        if level := self._ordered_level():
            order = self.library.game_order
            if 0 <= order.index(level.id) + offset < len(order):
                self._write(self.library.move_in_game_order, level.id, offset, success="Reihenfolge gespeichert")
            else:
                self.message = "Das Level steht bereits am Anfang oder Ende."

    @staticmethod
    def _open_rect(row):
        return pygame.Rect(row.right - 67, row.y + 1, 62, row.height - 2)

    def _open(self, level_id):
        level = self.library.levels[level_id]
        if level.available:
            self.open_draft(level.draft_name)
        else:
            self.message = f"Die Datei für „{level.name}“ fehlt."

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self._level():
                self._open(self.selected_level)
        elif event.type == pygame.MOUSEWHEEL:
            pos = getattr(event, "pos", pygame.mouse.get_pos())
            if self.design.collidepoint(pos):
                self.design_offset -= event.y * 3
            elif self.order.collidepoint(pos):
                self.order_offset -= event.y * 3
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._click(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragged_level:
            original = self.dragged_level
            self.dragged_level = None
            for rect, _, target, _ in self._rows(self.order):
                if target != original and rect.collidepoint(event.pos):
                    ordered = self.library.game_order
                    self._write(self.library.move_in_game_order, original,
                                ordered.index(target) - ordered.index(original), success="Reihenfolge gespeichert")
                    break

    def _click(self, pos):
        for rect, _, action in self._controls():
            if rect.collidepoint(pos):
                action()
                return
        for area in (self.design, self.order):
            if not area.collidepoint(pos):
                continue
            for rect, kind, item_id, _ in self._rows(area):
                if not rect.collidepoint(pos):
                    continue
                self.message = ""
                if kind == "world":
                    self.target_world = item_id
                    self.expanded.symmetric_difference_update({item_id})
                else:
                    self.selected_level = item_id
                    if self._open_rect(rect).collidepoint(pos):
                        self._open(item_id)
                    elif area == self.order:
                        self.dragged_level = item_id
                return

    def _text(self, screen, text, pos, width, color=TEXT):
        rendered = self.font.render(text, True, color)
        screen.blit(rendered, pos, area=(0, 0, width, rendered.get_height()))

    def draw(self, screen):
        pygame.draw.rect(screen, BG, self.panel)
        pygame.draw.rect(screen, SELECTED, self.panel, 2)
        self._text(screen, "WORLD STUDIO", (self.design.x, self.panel.y + 13), self.panel.width - 36, ACCENT)
        self._text(screen, "Level auswählen · Zielwelt anklicken · Zuordnen", (self.design.x, self.panel.y + 39),
                   self.panel.width - 36, MUTED)
        for area, title in ((self.design, "Entwurfsbibliothek"), (self.order, "Spielreihenfolge")):
            self._text(screen, title, (area.x, area.y - 24), area.width, ACCENT)
            pygame.draw.rect(screen, PANEL, area)
            for rect, kind, item_id, label in self._rows(area):
                if kind == "world":
                    selected = item_id == self.target_world
                    arrow = "−" if item_id in self.expanded else "+"
                    pygame.draw.rect(screen, SELECTED if selected else BUTTON, rect)
                    self._text(screen, f"{arrow}  {label}", (rect.x + 7, rect.y + 3), rect.width - 14)
                    continue
                selected = item_id == self.selected_level
                level = self.library.levels[item_id]
                pygame.draw.rect(screen, SELECTED if selected else PANEL, rect)
                self._text(screen, label if level.available else f"{label} (Datei fehlt)",
                           (rect.x + 13, rect.y + 3), rect.width - 86, TEXT if level.available else MUTED)
                if level.available:
                    button = self._open_rect(rect)
                    pygame.draw.rect(screen, BUTTON, button)
                    self._text(screen, "Öffnen", (button.x + 7, button.y + 2), button.width - 10)
        for rect, label, _ in self._controls():
            pygame.draw.rect(screen, BUTTON, rect)
            self._text(screen, label, (rect.x + 7, rect.y + 4), rect.width - 14)
        target = self.library.worlds.get(self.target_world)
        status = self.message or f"Zielwelt · {target.name if target else FREE_LABEL}"
        self._text(screen, status, (self.design.x, self.panel.bottom - 33), self.panel.width - 150, ACCENT)

"""DEV+ optional Snake-Head feedback dialog. No gameplay mutations."""
from collections import deque

import pygame

VERDICTS = (
    "Hilft", "Hilft nicht", "Zu schwach",
    "Zu stark", "Nicht kompatibel", "Neue Funktion gewünscht",
)


class DeveloperFeedbackUI:
    def __init__(self):
        self.queue = deque(maxlen=8)
        self.current = None
        self.rating = None
        self.note = ""
        self.item_index = 0
        self.flags = set()
        self.note_focused = False
        self._icons = {}
        self._fonts = {}

    @property
    def active(self):
        return self.current is not None

    def clear(self):
        self.queue.clear()
        self.current = None
        self.rating = None
        self.note = ""
        self.flags = set()
        self.item_index = 0
        self.note_focused = False

    def enqueue(self, subject, prompt, *, items=()):
        if len(self.queue) >= 8:
            return False
        self.queue.append((str(subject), str(prompt), tuple(items)[:12]))
        if not self.active:
            self._next()
        return True

    def _next(self):
        self.current = self.queue.popleft() if self.queue else None
        self.rating = None
        self.note = ""
        self.item_index = 0
        self.flags = set()
        self.note_focused = False

    def current_item(self):
        return self.current[2][self.item_index] if self.active and self.current[2] else None

    def choose_rating(self, rating):
        if self.active and type(rating) is int and 0 <= rating <= 5:
            self.rating = rating

    def toggle_verdict(self, verdict):
        if self.current_item() is None or verdict not in VERDICTS:
            return
        if verdict in self.flags:
            self.flags.remove(verdict)
        else:
            self.flags.add(verdict)

    def submit(self, recorder, *, save=True):
        if not self.active:
            return False
        subject, prompt, _ = self.current
        if self.current_item():
            subject = "item:" + self.current_item()
        if save and (self.rating is not None or self.note.strip() or self.flags):
            recorder.add_feedback(
                subject=subject, prompt=prompt, rating=self.rating,
                note=self.note.strip(), item_verdict=sorted(self.flags)
                if self.current_item() else None,
            )
        elif recorder.active:
            recorder.event("feedback_skipped", subject=subject)
        self._next()
        return True

    def _font(self, size, bold=False):
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont("Segoe UI", size, bold=bold)
        return self._fonts[key]

    def _layout(self, viewport):
        width, height = viewport
        panel = pygame.Rect(0, 0, max(260, min(700, width - 26)),
                            max(310, min(462, height - 20)))
        panel.center = (width // 2, height // 2)
        left, inner = panel.left + 18, panel.w - 36
        cell = min(65, max(35, (inner - 25) // 6))
        ratings = [pygame.Rect(left + (inner - 6 * cell) // 2 + i * cell,
                               panel.y + 163, cell - 5, 54) for i in range(6)]
        flags = [pygame.Rect(left + (i % 2) * (inner // 2),
                             panel.y + 225 + (i // 2) * 31,
                             inner // 2 - 6, 26) for i in range(6)]
        return {
            "panel": panel, "ratings": ratings, "flags": flags,
            "prev": pygame.Rect(left, panel.y + 108, 36, 32),
            "next": pygame.Rect(panel.right - 54, panel.y + 108, 36, 32),
            "note": pygame.Rect(left, panel.bottom - 106, inner, 37),
            "save": pygame.Rect(panel.right - 236, panel.bottom - 54, 104, 36),
            "skip": pygame.Rect(panel.right - 120, panel.bottom - 54, 104, 36),
        }

    def handle_event(self, event, recorder, viewport):
        if not self.active:
            return False
        r = self._layout(viewport)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return self.submit(recorder, save=False)
            if event.key == pygame.K_RETURN:
                return self.submit(recorder)
            if event.key == pygame.K_TAB:
                self.note_focused = not self.note_focused
            elif self.note_focused:
                if event.key == pygame.K_BACKSPACE:
                    self.note = self.note[:-1]
                elif event.unicode and event.unicode.isprintable() and len(self.note) < 500:
                    self.note += event.unicode
            elif pygame.K_0 <= event.key <= pygame.K_5:
                self.choose_rating(event.key - pygame.K_0)
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT) and self.current_item():
                self.item_index = (self.item_index + (-1 if event.key == pygame.K_LEFT else 1)) % len(self.current[2])
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if r["save"].collidepoint(pos):
                return self.submit(recorder)
            if r["skip"].collidepoint(pos):
                return self.submit(recorder, save=False)
            self.note_focused = r["note"].collidepoint(pos)
            for i, rect in enumerate(r["ratings"]):
                if rect.collidepoint(pos):
                    self.choose_rating(i)
                    return False
            if self.current_item():
                if r["prev"].collidepoint(pos):
                    self.item_index = (self.item_index - 1) % len(self.current[2])
                elif r["next"].collidepoint(pos):
                    self.item_index = (self.item_index + 1) % len(self.current[2])
                for i, rect in enumerate(r["flags"]):
                    if rect.collidepoint(pos):
                        self.toggle_verdict(VERDICTS[i])
                        return False
        return False

    def _line(self, screen, value, font, color, x, y, width):
        text = str(value)
        while text and font.size(text)[0] > width:
            text = text[:-2]
        if text:
            screen.blit(font.render(text, True, color), (x, y))

    def draw(self, screen, snake_icon=None):
        if not self.active:
            return
        r = self._layout(screen.get_size())
        p = r["panel"]
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((5, 8, 20, 169))
        screen.blit(shade, (0, 0))
        pygame.draw.rect(screen, (14, 19, 38), p, border_radius=14)
        pygame.draw.rect(screen, (119, 206, 225), p, 2, border_radius=14)
        small, label, title = self._font(15), self._font(17, True), self._font(22, True)
        self._line(screen, "IRIANS AUGE  |  DEV+ FEEDBACK", title, (168, 231, 248),
                   p.x + 18, p.y + 14, p.w - 36)
        self._line(screen, self.current[1], label, (235, 237, 246),
                   p.x + 18, p.y + 58, p.w - 36)
        item = self.current_item()
        if item:
            self._line(screen, "Eingesammeltes Item auswählen:", small,
                       (184, 214, 230), p.x + 18, p.y + 86, p.w - 36)
            for key, symbol in (("prev", "<"), ("next", ">")):
                pygame.draw.rect(screen, (38, 47, 73), r[key], border_radius=6)
                self._line(screen, symbol, label, (231, 239, 245),
                           r[key].x + 11, r[key].y + 5, 24)
            self._line(screen, item, label, (221, 192, 244), p.x + 64,
                       p.y + 113, p.w - 128)
        else:
            self._line(screen, "0 = schlecht / 5 = hervorragend", small,
                       (183, 211, 228), p.x + 18, p.y + 115, p.w - 36)
        for i, rect in enumerate(r["ratings"]):
            selected = self.rating == i
            pygame.draw.rect(screen, (40, 76, 69) if selected else (30, 39, 61),
                             rect, border_radius=7)
            pygame.draw.rect(screen, (141, 237, 185) if selected else (84, 109, 130),
                             rect, 2, border_radius=7)
            if i and snake_icon is not None:
                key = (id(snake_icon), 27)
                if key not in self._icons:
                    self._icons[key] = pygame.transform.smoothscale(snake_icon, (27, 27))
                icon = self._icons[key].copy()
                if not selected:
                    icon.set_alpha(140)
                screen.blit(icon, icon.get_rect(center=(rect.centerx, rect.y + 20)))
            else:
                text = label.render(str(i), True, (223, 236, 244))
                screen.blit(text, text.get_rect(center=(rect.centerx, rect.y + 20)))
            number = small.render(str(i), True, (192, 234, 244))
            screen.blit(number, number.get_rect(center=(rect.centerx, rect.y + 43)))
        if item:
            for value, rect in zip(VERDICTS, r["flags"]):
                pygame.draw.rect(screen, (43, 70, 65) if value in self.flags
                                 else (29, 36, 56), rect, border_radius=4)
                pygame.draw.rect(screen, (127, 210, 190), rect, 1, border_radius=4)
                self._line(screen, ("[x] " if value in self.flags else "[ ] ") + value,
                           small, (228, 242, 244), rect.x + 6, rect.y + 3, rect.w - 12)
        else:
            self._line(screen, "Optional: ein kurzer Satz zur Spielmechanik",
                       small, (184, 205, 230), p.x + 18, p.y + 258, p.w - 36)
        pygame.draw.rect(screen, (9, 13, 26), r["note"], border_radius=6)
        pygame.draw.rect(screen, (137, 226, 215) if self.note_focused
                         else (92, 122, 148), r["note"], 2, border_radius=6)
        self._line(screen, ("..." + self.note[-75:] if len(self.note) > 75 else self.note)
                   or "Kommentar optional (klicken oder TAB)",
                   small, (235, 239, 249) if self.note else (157, 171, 188),
                   r["note"].x + 8, r["note"].y + 8, r["note"].w - 16)
        for text, key, color in (("Speichern", "save", (47, 105, 88)),
                                 ("Überspringen", "skip", (63, 68, 88))):
            pygame.draw.rect(screen, color, r[key], border_radius=7)
            drawn = small.render(text, True, (247, 250, 251))
            screen.blit(drawn, drawn.get_rect(center=r[key].center))

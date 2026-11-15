"""Session-only visibility, solo and editing protection for World Studio."""

from dataclasses import dataclass, field


LAYER_LABELS = {
    "ground": "Boden",
    "objects": "Objekte",
    "roof": "Dach / Foreground",
    "collision": "Kollision",
    "effects": "Effekte",
}
LAYER_COLORS = {
    "ground": (134, 211, 156),
    "objects": (135, 186, 252),
    "roof": (252, 208, 134),
    "collision": (250, 165, 107),
    "effects": (211, 158, 245),
}


@dataclass(slots=True)
class LayerView:
    hidden: set[str] = field(default_factory=set)
    locked: set[str] = field(default_factory=set)
    solo: str | None = None

    def visible(self, layer):
        return self.solo == layer if self.solo is not None else layer not in self.hidden

    def show_all(self):
        self.solo = None
        self.hidden.clear()

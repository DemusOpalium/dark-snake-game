"""Non-blocking, data-driven visual effects for Dark Snake."""

from __future__ import annotations

import json
from dataclasses import dataclass

import pygame

from modules.resources import asset_roots


DEFAULTS = {"fps": 24, "loop": False, "opacity": 255, "scale": 1.0,
            "blend_mode": "normal", "layer": "world", "lifetime": 0.75}
SUPPORTED_EFFECTS = {"hit", "explosion", "smoke", "fog", "rain", "portal",
                     "boss_aura", "screen_flicker", "death", "spawn"}


@dataclass
class _Effect:
    name: str
    position: tuple[float, float]
    settings: dict
    frames: list[pygame.Surface]
    age: float = 0.0


class EffectManager:
    """Owns short-lived animations and removes them when they expire."""

    def __init__(self):
        self._effects: list[_Effect] = []
        self._cache: dict[str, tuple[dict, list[pygame.Surface]]] = {}

    def _load(self, name):
        if name in self._cache:
            return self._cache[name]
        config = dict(DEFAULTS)
        frames = []
        for root in asset_roots():
            folder = root / "effects" / name
            manifest = folder / "manifest.json"
            if manifest.is_file():
                try:
                    loaded = json.loads(manifest.read_text(encoding="utf-8"))
                    config.update({key: loaded[key] for key in DEFAULTS if key in loaded})
                except (OSError, ValueError, TypeError):
                    pass
            for path in sorted(folder.glob("frame_*.png")) + sorted(folder.glob("frame_*.webp")):
                try:
                    frames.append(pygame.image.load(str(path)).convert_alpha())
                except pygame.error:
                    continue
            if frames:
                break
        self._cache[name] = config, frames
        return self._cache[name]

    def spawn(self, effect_name, position, settings=None):
        """Spawn an effect. Unknown names are accepted for future asset packs."""
        manifest, frames = self._load(effect_name)
        options = dict(manifest)
        options.update(settings or {})
        effect = _Effect(effect_name, tuple(position), options, frames)
        self._effects.append(effect)
        return effect

    def update(self, delta_time):
        delta = max(0.0, float(delta_time))
        for effect in self._effects:
            effect.age += delta
        self._effects[:] = [effect for effect in self._effects
                            if effect.settings.get("loop") or
                            effect.age < max(0.001, float(effect.settings["lifetime"]))]

    def draw(self, surface, layer):
        for effect in self._effects:
            if effect.settings.get("layer") != layer:
                continue
            image = self._frame(effect)
            if image is None:
                self._draw_procedural(surface, effect)
                continue
            scale = max(0.01, float(effect.settings["scale"]))
            if scale != 1:
                image = pygame.transform.smoothscale(
                    image, (max(1, int(image.width * scale)), max(1, int(image.height * scale))))
            image = image.copy()
            image.set_alpha(max(0, min(255, int(effect.settings["opacity"]))))
            rect = image.get_rect(center=(round(effect.position[0]), round(effect.position[1])))
            flag = pygame.BLEND_ADD if effect.settings.get("blend_mode") == "add" else 0
            surface.blit(image, rect, special_flags=flag)

    def _frame(self, effect):
        if not effect.frames:
            return None
        index = int(effect.age * max(0.01, float(effect.settings["fps"])))
        if effect.settings.get("loop"):
            index %= len(effect.frames)
        return effect.frames[min(index, len(effect.frames) - 1)]

    @staticmethod
    def _draw_procedural(surface, effect):
        progress = min(1.0, effect.age / max(0.001, float(effect.settings["lifetime"])))
        radius = max(2, int(8 + progress * 24))
        alpha = int((1 - progress) * int(effect.settings["opacity"]))
        overlay = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        colors = {"smoke": (150, 150, 150), "fog": (190, 200, 210),
                  "portal": (145, 45, 255), "boss_aura": (255, 40, 80),
                  "rain": (80, 150, 255)}
        pygame.draw.circle(overlay, (*colors.get(effect.name, (255, 150, 40)), alpha),
                           (radius, radius), radius, max(1, radius // 4))
        surface.blit(overlay, overlay.get_rect(center=effect.position))

    def clear(self):
        self._effects.clear()

    def active_effects(self):
        return tuple(self._effects)

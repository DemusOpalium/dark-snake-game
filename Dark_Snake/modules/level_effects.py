"""Immutable settings shared by the level editor and its isolated playtest."""

from dataclasses import dataclass


SLOW_PERCENTAGES = (10, 25, 50, 75, 90)


@dataclass(frozen=True, slots=True)
class DamageField:
    amount: int = 10
    interval: float = 1.0
    duration: float | None = None

    def __post_init__(self):
        if type(self.amount) is not int or not 1 <= self.amount <= 100:
            raise ValueError("Schaden muss eine ganze Zahl von 1 bis 100 HP sein.")
        if type(self.interval) not in (int, float) or not 0.1 <= self.interval <= 60:
            raise ValueError("Das Trefferintervall muss zwischen 0,1 und 60 Sekunden liegen.")
        if self.duration is not None and (
                type(self.duration) not in (int, float) or not 0.1 <= self.duration <= 600):
            raise ValueError("Die Wirkungsdauer muss zwischen 0,1 und 600 Sekunden liegen.")


@dataclass(frozen=True, slots=True)
class SlowField:
    percent: int = 50

    def __post_init__(self):
        if type(self.percent) is not int or self.percent not in SLOW_PERCENTAGES:
            raise ValueError("Erlaubte Verlangsamung sind 10, 25, 50, 75 oder 90 Prozent.")


@dataclass(frozen=True, slots=True)
class CellEffects:
    damage: DamageField | None = None
    slow: SlowField | None = None

    def __post_init__(self):
        if self.damage is not None and not isinstance(self.damage, DamageField):
            raise ValueError("Ungültiges Schadensfeld.")
        if self.slow is not None and not isinstance(self.slow, SlowField):
            raise ValueError("Ungültiges Verlangsamungsfeld.")


EffectCells = dict[tuple[int, int], CellEffects]

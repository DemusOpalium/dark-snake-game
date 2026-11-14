"""Visibility settings shared by the roof editor and renderer."""

from dataclasses import dataclass

from modules.frostage_assets import frostage_assets


@dataclass(frozen=True, slots=True)
class RoofVisibility:
    """Measure the radius and falloff in cells and transparency in percent."""

    enabled: bool = True
    radius: float = 2.0
    transparency: int = 75
    softness: float = 1.0

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError("Das Dach-Sichtfenster muss ein- oder ausgeschaltet sein.")
        if type(self.radius) not in (int, float) or not 0.5 <= self.radius <= 6:
            raise ValueError("Der Sichtradius muss zwischen 0,5 und 6 Rasterfeldern liegen.")
        if type(self.transparency) is not int or not 0 <= self.transparency <= 100:
            raise ValueError("Die Dachtransparenz muss eine ganze Zahl von 0 bis 100 Prozent sein.")
        if type(self.softness) not in (int, float) or not 0 <= self.softness <= self.radius:
            raise ValueError("Die Randweichheit muss zwischen null und dem Sichtradius liegen.")


def is_roof_asset(asset_id: str) -> bool:
    asset = frostage_assets().get(asset_id)
    return asset is not None and asset.category == "roof"

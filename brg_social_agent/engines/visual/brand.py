from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import Config


@dataclass(frozen=True)
class BrandContext:
    primary_color: str
    accent_color: str
    font_family: str
    logo_svg: str
    headshot_path: Optional[str]


def load_brand_context(config: Config) -> BrandContext:
    logo_svg = ""
    logo_path = Path(config.logo_path)
    if logo_path.exists():
        logo_svg = logo_path.read_text(encoding="utf-8")

    headshot_path: Optional[str] = None
    hs_path = Path(config.headshot_path)
    if hs_path.exists():
        headshot_path = str(hs_path.resolve())

    return BrandContext(
        primary_color=config.brand_primary_color,
        accent_color=config.brand_accent_color,
        font_family=config.brand_font_family,
        logo_svg=logo_svg,
        headshot_path=headshot_path,
    )

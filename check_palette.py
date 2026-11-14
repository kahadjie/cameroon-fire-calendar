"""Vérifie la palette de index.html en niveaux de gris : la luminance doit croître d'une classe à l'autre,
avec un écart visible, pour que l'ordre des couleurs se lise sans la couleur. Lancer : python check_palette.py"""

import re
import sys
from pathlib import Path

html = Path(__file__).with_name("index.html").read_text(encoding="utf-8")
palette = re.search(r"const PALETTE = \[(.*?)\];", html).group(1)
colors = re.findall(r"#[0-9a-fA-F]{6}", palette)


def luminance(hex_color: str) -> float:
    """Luminance relative WCAG 2.x (0 noir, 1 blanc)."""
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def gray(hex_color: str) -> int:
    """Niveau de gris perçu (0-255), formule Rec. 709 sur les valeurs gamma."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return round(0.2126 * r + 0.7152 * g + 0.0722 * b)


ok = True
previous = None
for i, c in enumerate(colors):
    lum, g = luminance(c), gray(c)
    step = "" if previous is None else f"  écart de gris {g - previous}"
    print(f"classe {i} {c}  luminance {lum:.3f}  gris {g:3d}{step}")
    if previous is not None and g - previous < 12:
        ok = False
    previous = g
print("Palette monotone en niveaux de gris, écart >= 12 entre classes :", "OUI" if ok else "NON")
sys.exit(0 if ok else 1)

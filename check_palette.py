"""Checks the index.html palette in grayscale: luminance must increase from one class to the next, with a
visible step, so the order of colors can be read without color. Run: python check_palette.py"""

import re
import sys
from pathlib import Path

html = Path(__file__).with_name("index.html").read_text(encoding="utf-8")
palette = re.search(r"const PALETTE = \[(.*?)\];", html).group(1)
colors = re.findall(r"#[0-9a-fA-F]{6}", palette)


def luminance(hex_color: str) -> float:
    """WCAG 2.x relative luminance (0 black, 1 white)."""
    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def gray(hex_color: str) -> int:
    """Perceived gray level (0-255), Rec. 709 weights on gamma-encoded values."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return round(0.2126 * r + 0.7152 * g + 0.0722 * b)


ok = True
previous = None
for i, c in enumerate(colors):
    lum, g = luminance(c), gray(c)
    step = "" if previous is None else f"  gray step {g - previous}"
    print(f"class {i} {c}  luminance {lum:.3f}  gray {g:3d}{step}")
    if previous is not None and g - previous < 12:
        ok = False
    previous = g
print("Palette increases in grayscale, step >= 12 between classes:", "YES" if ok else "NO")
sys.exit(0 if ok else 1)

#!/usr/bin/env python3
"""Generate self-contained SVG glyph comparisons from TTF outlines."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


WIDTH = 1440
LEFT = 250
CELL_WIDTH = 370
COLORS = ("#64748b", "#0f766e", "#0369a1")
HEADERS = ("Upstream Bold", "Clear Code Bold", "Clear Code Regular")
GRID_LABELS = (
    "Upstream Bold",
    "Upstream Regular",
    "Clear Code Bold",
    "Clear Code Regular",
)
GRID_COLORS = ("#475569", "#64748b", "#0f766e", "#0369a1")


def font_paths(repo: Path, upstream: Path, italic: bool) -> tuple[Path, Path, Path]:
    suffix = "BoldItalic.ttf" if italic else "Bold.ttf"
    regular = "Italic.ttf" if italic else "Regular.ttf"
    return (
        upstream / f"SauceCodeProNerdFont-{suffix}",
        repo / "fonts" / "ClearCodePro" / f"ClearCodePro-{suffix}",
        repo / "fonts" / "ClearCodePro" / f"ClearCodePro-{regular}",
    )


def grid_font_paths(
    repo: Path, upstream: Path, italic: bool
) -> tuple[Path, Path, Path, Path]:
    bold = "BoldItalic.ttf" if italic else "Bold.ttf"
    regular = "Italic.ttf" if italic else "Regular.ttf"
    return (
        upstream / f"SauceCodeProNerdFont-{bold}",
        upstream / f"SauceCodeProNerdFont-{regular}",
        repo / "fonts" / "ClearCodePro" / f"ClearCodePro-{bold}",
        repo / "fonts" / "ClearCodePro" / f"ClearCodePro-{regular}",
    )


def outlined_text(font_path: Path, text: str, x: float, baseline: float,
                  size: float, color: str) -> str:
    font = TTFont(font_path)
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    units_per_em = font["head"].unitsPerEm
    scale = size / units_per_em
    runs: list[tuple[str, int]] = []
    total_advance = 0

    for character in text:
        glyph_name = cmap[ord(character)]
        pen = SVGPathPen(glyphs)
        glyphs[glyph_name].draw(pen)
        advance = font["hmtx"][glyph_name][0]
        runs.append((pen.getCommands(), total_advance))
        total_advance += advance

    start_x = x - total_advance * scale / 2
    paths = []
    for commands, advance in runs:
        paths.append(
            f'<path d="{commands}" transform="translate({start_x + advance * scale:.2f} '
            f'{baseline:.2f}) scale({scale:.6f} {-scale:.6f})" fill="{color}"/>'
        )
    font.close()
    return "\n".join(paths)


def svg_start(height: int, title: str, subtitle: str) -> list[str]:
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{html.escape(title)}</title>",
        f"<desc id=\"desc\">{html.escape(subtitle)}</desc>",
        '<rect width="100%" height="100%" rx="24" fill="#f8fafc"/>',
        '<style>text{font-family:Inter,Segoe UI,Arial,sans-serif}'
        '.title{font-size:30px;font-weight:700;fill:#0f172a}'
        '.subtitle{font-size:16px;fill:#475569}'
        '.header{font-size:16px;font-weight:700}'
        '.row{font-size:17px;font-weight:600;fill:#334155}'
        '.hint{font-size:14px;fill:#64748b}</style>',
        f'<text class="title" x="40" y="48">{html.escape(title)}</text>',
        f'<text class="subtitle" x="40" y="77">{html.escape(subtitle)}</text>',
    ]


def comparison_svg(repo: Path, upstream: Path, glyph: str, name: str) -> str:
    height = 930
    parts = svg_start(
        height,
        f"{name} ({glyph})",
        "SauceCodePro Nerd Font 3.4.0 compared with Clear Code Pro",
    )
    for section, (style, italic) in enumerate((("Upright", False), ("Italic", True))):
        section_y = 108 + section * 410
        parts.append(f'<text class="row" x="32" y="{section_y}">{style}</text>')
        for index, (font_path, label, color) in enumerate(
            zip(grid_font_paths(repo, upstream, italic), GRID_LABELS, GRID_COLORS)
        ):
            column = index % 2
            row = index // 2
            x = 24 + column * 704
            y = section_y + 18 + row * 178
            parts.append(
                f'<rect x="{x}" y="{y}" width="688" height="164" rx="14" '
                'fill="#ffffff" stroke="#e2e8f0"/>'
            )
            parts.append(
                f'<text class="header" x="{x + 24}" y="{y + 30}" '
                f'fill="{color}">{label}</text>'
            )
            parts.append(
                outlined_text(font_path, glyph, x + 260, y + 122, 88, color)
            )
            parts.append(
                outlined_text(font_path, glyph, x + 515, y + 112, 22, color)
            )
            parts.append(
                f'<text class="hint" x="{x + 260}" y="{y + 150}" '
                'text-anchor="middle">Large</text>'
            )
            parts.append(
                f'<text class="hint" x="{x + 515}" y="{y + 150}" '
                'text-anchor="middle">Small</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def distinction_svg(repo: Path, upstream: Path) -> str:
    height = 520
    sample = "1|ilIL!"
    parts = svg_start(
        height,
        f"Character distinction: {sample}",
        "Side-by-side distinction comparison at large and small sizes",
    )
    for column, (header, color) in enumerate(zip(HEADERS, COLORS)):
        center = LEFT + column * CELL_WIDTH + CELL_WIDTH / 2
        parts.append(
            f'<text class="header" x="{center}" y="116" text-anchor="middle" '
            f'fill="{color}">{header}</text>'
        )
    rows = (
        ("Large · Upright", False, 68, 215),
        ("Small · Upright", False, 20, 345),
        ("Small · Italic", True, 20, 455),
    )
    for index, (label, italic, size, baseline) in enumerate(rows):
        top = (126, 270, 380)[index]
        parts.append(f'<rect x="24" y="{top}" width="1392" height="{124 if index == 0 else 96}" '
                     'rx="14" fill="#ffffff" stroke="#e2e8f0"/>')
        parts.append(f'<text class="row" x="48" y="{baseline - 15}">{label}</text>')
        for column, (font_path, color) in enumerate(
            zip(font_paths(repo, upstream, italic), COLORS)
        ):
            center = LEFT + column * CELL_WIDTH + CELL_WIDTH / 2
            parts.append(outlined_text(font_path, sample, center, baseline, size, color))
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--upstream-dir",
        required=True,
        type=Path,
        help="Directory containing the Nerd Fonts 3.4.0 SourceCodePro TTF files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/glyph-previews"),
    )
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    output = (repo / args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    glyphs = (
        ("0", "zero"),
        ("1", "one"),
        ("~", "tilde"),
        ("!", "exclamation"),
        ("%", "percent"),
        ("&", "ampersand"),
    )
    for glyph, name in glyphs:
        (output / f"{name}.svg").write_text(
            comparison_svg(repo, args.upstream_dir.resolve(), glyph, name.title()),
            encoding="utf-8",
        )
    (output / "character-distinction.svg").write_text(
        distinction_svg(repo, args.upstream_dir.resolve()),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

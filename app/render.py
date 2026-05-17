from dataclasses import dataclass
from typing import Optional

from .themes import Theme

_FONT = "'Fira Code', 'Courier New', monospace"

# ── Progress bar (disabled — saved for future live-progress widget) ───────────
# Restore _BAR_W and _progress_bar() when re-enabling, and add progress: float
# back to CardData. The bar rendered below the series/author line.
#
# _BAR_W = _TEXT_RIGHT - _TEXT_X - 40
#
# def _progress_bar(bar_top: int, progress: float, theme: Theme) -> str:
#     fill_w = max(0, int(_BAR_W * progress))
#     pct = f"{int(progress * 100)}%"
#     pct_x = _TEXT_X + _BAR_W + 6
#     bar_y = bar_top + 6
#     return (
#         f'<rect x="{_TEXT_X}" y="{bar_top}" width="{_BAR_W}" height="6"'
#         f' rx="3" fill="{theme.border}"/>'
#         f'<rect x="{_TEXT_X}" y="{bar_top}" width="{fill_w}" height="6"'
#         f' rx="3" fill="{theme.accent}"/>'
#         f'<text x="{pct_x}" y="{bar_y}" font-family="{_FONT}" font-size="11"'
#         f' fill="{theme.text_secondary}" dominant-baseline="auto">{pct}</text>'
#     )
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class CardData:
    title: str
    author: str
    series: Optional[str]
    cover_b64: Optional[str]
    narrator: Optional[str]
    publisher: Optional[str]
    year: Optional[str]


# ── Shared helpers ────────────────────────────────────────────────────────────

def _x(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _bg(w: int, h: int, theme: Theme) -> str:
    return (
        f'<rect width="{w}" height="{h}" rx="10"'
        f' fill="{theme.background}" stroke="{theme.border}" stroke-width="1"/>'
    )


def _cover(
    x: int, y: int, w: int, h: int,
    cover_b64: Optional[str], theme: Theme,
    clip_id: str = "cc",
) -> str:
    if cover_b64:
        return (
            f'<defs><clipPath id="{clip_id}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>'
            f'</clipPath></defs>'
            f'<image href="{cover_b64}" x="{x}" y="{y}" width="{w}" height="{h}"'
            f' clip-path="url(#{clip_id})" preserveAspectRatio="xMidYMid slice"/>'
        )
    mid_x = x + w // 2
    mid_y = y + h // 2
    fs = min(48, w // 3)
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{theme.border}"/>'
        f'<text x="{mid_x}" y="{mid_y + fs // 3}" font-size="{fs}" text-anchor="middle"'
        f' font-family="serif" fill="{theme.text_secondary}">&#128214;</text>'
    )


# ── Demo data ─────────────────────────────────────────────────────────────────

_DEMO_DATA = CardData(
    title="Project Hail Mary",
    author="Andy Weir",
    series=None,
    cover_b64=None,
    narrator="Ray Porter",
    publisher="Ballantine Books",
    year="2021",
)


# ── Landscape card (600×160) ──────────────────────────────────────────────────
#
#  ┌──────────────────────────────────────────────────────────────────────┐
#  │            │                          │                              │
#  │  [COVER]   │  Currently Reading       │  Publisher  Del Rey          │
#  │  128×128   │  Project Hail Mary       │  Year       2021             │
#  │            │  Andy Weir               │                              │
#  │            │  Narrated by Ray Porter  │  Series  Exp. Force · Bk 1   │
#  │            │                          │                              │
#  └──────────────────────────────────────────────────────────────────────┘

_LS_W = 600
_LS_H = 160
_LS_COVER_X = 16
_LS_COVER_Y = 16
_LS_COVER_W = 128
_LS_COVER_H = 128
_LS_PRIMARY_X = 160
_LS_SEP_X = 355
_LS_META_X = 372


def render_landscape(theme: Theme, data: CardData, label: str = "Currently Reading") -> str:
    # Primary zone — 3 lines only (label, title, author), spread evenly in cover height
    y_label, y_title, y_author = 30, 62, 88

    title  = _x(_trunc(data.title, 26))
    author = _x(_trunc(data.author, 28))

    # Metadata zone — narrator first, then publisher·year, then series
    meta_lines = []
    if data.narrator:
        meta_lines.append(_x(_trunc(f'Narrated by {data.narrator}', 28)))
    pubyr_parts = [p for p in [data.publisher, data.year] if p]
    if pubyr_parts:
        meta_lines.append(_x(_trunc(" · ".join(pubyr_parts), 28)))
    if data.series:
        meta_lines.append(_x(_trunc(data.series, 28)))

    meta_line_h = 22
    meta_start  = y_label
    meta_els = "".join(
        f'  <text x="{_LS_META_X}" y="{meta_start + i * meta_line_h}"'
        f' font-family="{_FONT}" font-size="11" fill="{theme.text_secondary}">'
        f'{line}</text>\n'
        for i, line in enumerate(meta_lines)
    )

    sep = (
        f'  <line x1="{_LS_SEP_X}" y1="20" x2="{_LS_SEP_X}" y2="140"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
    )

    return (
        f'<svg width="{_LS_W}" height="{_LS_H}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  {_bg(_LS_W, _LS_H, theme)}\n'
        f'  {_cover(_LS_COVER_X, _LS_COVER_Y, _LS_COVER_W, _LS_COVER_H, data.cover_b64, theme)}\n'
        f'  <text x="{_LS_PRIMARY_X}" y="{y_label}" font-family="{_FONT}"'
        f' font-size="10" fill="{theme.text_secondary}">{_x(label)}</text>\n'
        f'  <text x="{_LS_PRIMARY_X}" y="{y_title}" font-family="{_FONT}"'
        f' font-size="14" font-weight="600" fill="{theme.text_primary}">{title}</text>\n'
        f'  <text x="{_LS_PRIMARY_X}" y="{y_author}" font-family="{_FONT}"'
        f' font-size="12" fill="{theme.text_secondary}">{author}</text>\n'
        f'{sep}'
        f'{meta_els}'
        f'</svg>'
    )


def _ls_status_card(theme: Theme, message: str) -> str:
    cx = _LS_W // 2
    return (
        f'<svg width="{_LS_W}" height="{_LS_H}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  {_bg(_LS_W, _LS_H, theme)}\n'
        f'  <text x="{cx}" y="{_LS_H // 2 + 5}" font-family="{_FONT}" font-size="13"'
        f' fill="{theme.text_secondary}" text-anchor="middle">{_x(message)}</text>\n'
        f'</svg>'
    )


def render_landscape_demo(theme: Theme) -> str:
    return render_landscape(theme, _DEMO_DATA, label="Demo — configure credentials to go live")


def render_landscape_nothing_playing(theme: Theme) -> str:
    return _ls_status_card(theme, "No listening history yet")


def render_landscape_error(theme: Theme) -> str:
    return _ls_status_card(theme, "Unable to reach Audiobookshelf")


# ── Portrait / trading card (240×360) ─────────────────────────────────────────
#
#  ┌─────────────────────────┐
#  │                         │
#  │        [COVER]          │
#  │        208×208          │
#  │                         │
#  ├─────────────────────────┤
#  │  Currently Reading      │
#  │  Project Hail Mary      │
#  │  Andy Weir              │
#  │  Narrated by Ray Porter │
#  │  Ballantine Books·2021  │
#  │  Series Name · Bk 1     │
#  └─────────────────────────┘

_PT_W       = 240
_PT_H       = 360
_PT_PAD     = 16
_PT_COVER_W = _PT_W - 2 * _PT_PAD        # 208
_PT_COVER_H = _PT_COVER_W                # 208 — square
_PT_COVER_X = _PT_PAD
_PT_COVER_Y = _PT_PAD
_PT_DIV_Y   = _PT_COVER_Y + _PT_COVER_H + 8   # 232


def render_portrait(theme: Theme, data: CardData, label: str = "Currently Reading") -> str:
    title  = _x(_trunc(data.title, 22))
    author = _x(_trunc(data.author, 24))

    # Build ordered list of (font_size, bold, content) for text below divider
    lines: list[tuple[int, bool, str]] = [
        (10, False, _x(label)),
        (14, True,  title),
        (12, False, author),
    ]
    if data.narrator:
        lines.append((11, False, f'Narrated by {_x(_trunc(data.narrator, 18))}'))
    pubyr_parts = [p for p in [data.publisher, data.year] if p]
    if pubyr_parts:
        lines.append((11, False, _x(_trunc(" · ".join(pubyr_parts), 24))))
    if data.series:
        lines.append((11, False, _x(_trunc(data.series, 24))))

    y = _PT_DIV_Y + 22
    text_els = ""
    for size, bold, content in lines:
        weight = ' font-weight="600"' if bold else ""
        color  = theme.text_primary if bold else theme.text_secondary
        text_els += (
            f'  <text x="{_PT_PAD}" y="{y}" font-family="{_FONT}"'
            f' font-size="{size}"{weight} fill="{color}">{content}</text>\n'
        )
        y += size + 7

    divider = (
        f'  <line x1="{_PT_PAD}" y1="{_PT_DIV_Y}"'
        f' x2="{_PT_W - _PT_PAD}" y2="{_PT_DIV_Y}"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
    )

    return (
        f'<svg width="{_PT_W}" height="{_PT_H}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  {_bg(_PT_W, _PT_H, theme)}\n'
        f'  {_cover(_PT_COVER_X, _PT_COVER_Y, _PT_COVER_W, _PT_COVER_H, data.cover_b64, theme, clip_id="pc")}\n'
        f'{divider}'
        f'{text_els}'
        f'</svg>'
    )


def _pt_status_card(theme: Theme, message: str) -> str:
    cx = _PT_W // 2
    cy = _PT_COVER_Y + _PT_COVER_H + (_PT_H - _PT_COVER_Y - _PT_COVER_H) // 2
    return (
        f'<svg width="{_PT_W}" height="{_PT_H}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  {_bg(_PT_W, _PT_H, theme)}\n'
        f'  <text x="{cx}" y="{cy}" font-family="{_FONT}" font-size="11"'
        f' fill="{theme.text_secondary}" text-anchor="middle">{_x(message)}</text>\n'
        f'</svg>'
    )


def render_portrait_demo(theme: Theme) -> str:
    return render_portrait(theme, _DEMO_DATA, label="Demo — configure credentials")


def render_portrait_nothing_playing(theme: Theme) -> str:
    return _pt_status_card(theme, "No listening history yet")


def render_portrait_error(theme: Theme) -> str:
    return _pt_status_card(theme, "Unable to reach Audiobookshelf")

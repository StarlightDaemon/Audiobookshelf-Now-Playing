from dataclasses import dataclass
from typing import Optional

from .themes import Theme

# Card geometry
_W = 495
_H = 128
_COVER_X = 16
_COVER_Y = 16
_COVER_W = 96
_COVER_H = 96
_TEXT_X = 128
_TEXT_RIGHT = _W - 16
# Progress bar ends 40px from right edge; percentage text fills that gap
_BAR_W = _TEXT_RIGHT - _TEXT_X - 40

_FONT = "'Fira Code', 'Courier New', monospace"


@dataclass
class CardData:
    title: str
    author: str
    series: Optional[str]
    progress: float  # 0.0–1.0
    cover_b64: Optional[str]  # data URI or None


def _x(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _cover(cover_b64: Optional[str], theme: Theme) -> str:
    cx, cy, cw, ch = _COVER_X, _COVER_Y, _COVER_W, _COVER_H
    if cover_b64:
        return (
            f'<defs><clipPath id="cc">'
            f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="6"/>'
            f'</clipPath></defs>'
            f'<image href="{cover_b64}" x="{cx}" y="{cy}" width="{cw}" height="{ch}"'
            f' clip-path="url(#cc)" preserveAspectRatio="xMidYMid slice"/>'
        )
    # Placeholder: subtle filled rect with a centered book icon (text glyph)
    mid_x = cx + cw // 2
    mid_y = cy + ch // 2
    return (
        f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="6" fill="{theme.border}"/>'
        f'<text x="{mid_x}" y="{mid_y + 10}" font-size="32" text-anchor="middle"'
        f' font-family="serif" fill="{theme.text_secondary}">&#128214;</text>'
    )


def _progress_bar(bar_top: int, progress: float, theme: Theme) -> str:
    fill_w = max(0, int(_BAR_W * progress))
    pct = f"{int(progress * 100)}%"
    pct_x = _TEXT_X + _BAR_W + 6
    bar_y = bar_top + 6  # baseline aligned with bottom of bar

    return (
        f'<rect x="{_TEXT_X}" y="{bar_top}" width="{_BAR_W}" height="6"'
        f' rx="3" fill="{theme.border}"/>'
        f'<rect x="{_TEXT_X}" y="{bar_top}" width="{fill_w}" height="6"'
        f' rx="3" fill="{theme.accent}"/>'
        f'<text x="{pct_x}" y="{bar_y}" font-family="{_FONT}" font-size="11"'
        f' fill="{theme.text_secondary}" dominant-baseline="auto">{pct}</text>'
    )


def _bg(theme: Theme) -> str:
    return (
        f'<rect width="{_W}" height="{_H}" rx="10"'
        f' fill="{theme.background}" stroke="{theme.border}" stroke-width="1"/>'
    )


_DEMO_DATA = CardData(
    title="Project Hail Mary",
    author="Andy Weir",
    series=None,
    progress=0.62,
    cover_b64=None,
)


def render_card(theme: Theme, data: CardData, label: str = "Currently Reading") -> str:
    has_series = bool(data.series)

    if has_series:
        y_label, y_title, y_author, y_series, bar_top = 27, 46, 63, 79, 94
    else:
        y_label, y_title, y_author, bar_top = 30, 50, 68, 87
        y_series = 0

    title = _x(_trunc(data.title, 38))
    author = _x(_trunc(data.author, 44))

    series_el = ""
    if has_series:
        series = _x(_trunc(data.series, 50))
        series_el = (
            f'<text x="{_TEXT_X}" y="{y_series}" font-family="{_FONT}"'
            f' font-size="11" fill="{theme.text_secondary}">{series}</text>'
        )

    return (
        f'<svg width="{_W}" height="{_H}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  {_bg(theme)}\n'
        f'  {_cover(data.cover_b64, theme)}\n'
        f'  <text x="{_TEXT_X}" y="{y_label}" font-family="{_FONT}"'
        f' font-size="11" fill="{theme.text_secondary}">{_x(label)}</text>\n'
        f'  <text x="{_TEXT_X}" y="{y_title}" font-family="{_FONT}"'
        f' font-size="14" font-weight="600" fill="{theme.text_primary}">{title}</text>\n'
        f'  <text x="{_TEXT_X}" y="{y_author}" font-family="{_FONT}"'
        f' font-size="12" fill="{theme.text_secondary}">{author}</text>\n'
        f'  {series_el}\n'
        f'  {_progress_bar(bar_top, data.progress, theme)}\n'
        f'</svg>'
    )


def render_demo(theme: Theme) -> str:
    return render_card(theme, _DEMO_DATA, label="Demo — configure credentials to go live")


def render_nothing_playing(theme: Theme) -> str:
    cx = _W // 2
    return (
        f'<svg width="{_W}" height="{_H}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  {_bg(theme)}\n'
        f'  <text x="{cx}" y="{_H // 2 + 5}" font-family="{_FONT}" font-size="13"'
        f' fill="{theme.text_secondary}" text-anchor="middle">'
        f'No listening history yet</text>\n'
        f'</svg>'
    )


def render_error(theme: Theme) -> str:
    cx = _W // 2
    return (
        f'<svg width="{_W}" height="{_H}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  {_bg(theme)}\n'
        f'  <text x="{cx}" y="{_H // 2 + 5}" font-family="{_FONT}" font-size="13"'
        f' fill="{theme.text_secondary}" text-anchor="middle">'
        f'Unable to reach Audiobookshelf</text>\n'
        f'</svg>'
    )

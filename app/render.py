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
    progress: Optional[float] = None


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


def _progress_bar(
    x: int, y: int, w: int,
    progress: Optional[float],
    theme: Theme,
    bar_h: int = 4,
    show_pct: bool = True,
) -> str:
    if progress is None:
        return ""
    pct_label = f"{int(progress * 100)}%"
    pct_w = 28 if show_pct else 0
    track_w = w - pct_w
    fill_w = max(0, int(track_w * min(progress, 1.0)))
    out = (
        f'<rect x="{x}" y="{y}" width="{track_w}" height="{bar_h}"'
        f' rx="{bar_h // 2}" fill="{theme.border}"/>'
        f'<rect x="{x}" y="{y}" width="{fill_w}" height="{bar_h}"'
        f' rx="{bar_h // 2}" fill="{theme.accent}"/>'
    )
    if show_pct:
        out += (
            f'<text x="{x + track_w + 6}" y="{y + bar_h}"'
            f' font-family="{_FONT}" font-size="9" fill="{theme.text_secondary}"'
            f' dominant-baseline="auto">{pct_label}</text>'
        )
    return out


# ── Demo data ─────────────────────────────────────────────────────────────────

_DEMO_DATA = CardData(
    title="Project Hail Mary",
    author="Andy Weir",
    series="The Weir Trilogy · Book 2",
    cover_b64=None,
    narrator="Ray Porter",
    publisher="Ballantine Books",
    year="2021",
    progress=0.62,
)

_DEMO_DATA_STANDALONE = CardData(
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
    # Primary zone — evenly distributed across full card height (content area y=20..140)
    y_label, y_title, y_author = 50, 80, 110

    title  = _x(_trunc(data.title, 26))
    author = _x(_trunc(data.author, 28))

    # Metadata zone — narrator first, then publisher·year, then series
    # Each entry: (text, muted) — muted=True renders at half opacity
    meta_lines: list[tuple[str, bool]] = []
    if data.narrator:
        meta_lines.append((_x(_trunc(f'Narrated by {data.narrator}', 28)), False))
    pubyr_parts = [p for p in [data.publisher, data.year] if p]
    if pubyr_parts:
        meta_lines.append((_x(_trunc(" · ".join(pubyr_parts), 28)), False))
    if data.series:
        meta_lines.append((_x(_trunc(data.series, 28)), False))
    else:
        meta_lines.append(("Standalone", True))

    meta_line_h = 30
    # Vertically center the meta block around the card midpoint (y=80)
    meta_start  = 80 - ((len(meta_lines) - 1) * meta_line_h) // 2
    meta_els = "".join(
        f'  <text x="{_LS_META_X}" y="{meta_start + i * meta_line_h}"'
        f' font-family="{_FONT}" font-size="11" fill="{theme.text_secondary}"'
        f'{" opacity=\"0.45\" font-style=\"italic\"" if muted else ""}>'
        f'{line}</text>\n'
        for i, (line, muted) in enumerate(meta_lines)
    )

    sep = (
        f'  <line x1="{_LS_SEP_X}" y1="20" x2="{_LS_SEP_X}" y2="140"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
    )

    bar = _progress_bar(_LS_PRIMARY_X, 130, _LS_SEP_X - _LS_PRIMARY_X - 8,
                        data.progress, theme)

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
        f'  {bar}\n'
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


def render_landscape_demo(theme: Theme, label: Optional[str] = None) -> str:
    return render_landscape(theme, _DEMO_DATA, label=label or "Demo — configure credentials to go live")


def render_landscape_standalone_demo(theme: Theme) -> str:
    return render_landscape(theme, _DEMO_DATA_STANDALONE, label="Demo — standalone book")


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

    bar = _progress_bar(_PT_PAD, _PT_H - 12, _PT_W - 2 * _PT_PAD,
                        data.progress, theme, show_pct=False)

    return (
        f'<svg width="{_PT_W}" height="{_PT_H}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  {_bg(_PT_W, _PT_H, theme)}\n'
        f'  {_cover(_PT_COVER_X, _PT_COVER_Y, _PT_COVER_W, _PT_COVER_H, data.cover_b64, theme, clip_id="pc")}\n'
        f'{divider}'
        f'{text_els}'
        f'  {bar}\n'
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


def render_portrait_demo(theme: Theme, label: Optional[str] = None) -> str:
    return render_portrait(theme, _DEMO_DATA, label=label or "Demo — configure credentials")


def render_portrait_nothing_playing(theme: Theme) -> str:
    return _pt_status_card(theme, "No listening history yet")


def render_portrait_error(theme: Theme) -> str:
    return _pt_status_card(theme, "Unable to reach Audiobookshelf")


# ── Layout B — Full-bleed cover + gradient overlay (240×360) ─────────────────
#
#  ┌──────────────────────────┐
#  │                          │
#  │   [cover fills card,     │
#  │    fades to dark at      │
#  │    bottom 40%]           │
#  │                          │
#  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ ← gradient starts
#  │  Currently Reading       │
#  │  Project Hail Mary       │
#  │  Andy Weir               │
#  │  Narrated by Ray Porter  │
#  └──────────────────────────┘

def render_portrait_b(theme: Theme, data: CardData, label: str = "Currently Reading") -> str:
    w, h = _PT_W, _PT_H
    pad  = _PT_PAD

    # Text lines (bottom section, starting ~y=220)
    title  = _x(_trunc(data.title,  22))
    author = _x(_trunc(data.author, 24))
    lines: list[tuple[int, bool, str]] = [
        (10, False, _x(label)),
        (15, True,  title),
        (12, False, author),
    ]
    if data.narrator:
        lines.append((11, False, f'Narrated by {_x(_trunc(data.narrator, 20))}'))
    pubyr_parts = [p for p in [data.publisher, data.year] if p]
    if pubyr_parts:
        lines.append((11, False, _x(_trunc(" · ".join(pubyr_parts), 26))))
    if data.series:
        lines.append((11, False, _x(_trunc(data.series, 26))))
    else:
        lines.append((11, False, "Standalone"))

    # Pin text block to bottom, grow upward
    line_gap = 6
    block_h = sum(s + line_gap for s, _, _ in lines)
    y_start = h - pad - block_h + lines[0][0]

    has_cover = bool(data.cover_b64)
    text_els = ""
    y = y_start
    for size, bold, content in lines:
        weight = ' font-weight="600"' if bold else ""
        muted  = content == "Standalone"
        if has_cover:
            color      = "#ffffff"
            fill_extra = "" if bold else ' fill-opacity="0.75"'
        else:
            color      = theme.text_primary if bold else theme.text_secondary
            fill_extra = ""
        italic = ' font-style="italic"' if muted else ""
        text_els += (
            f'  <text x="{pad}" y="{y}" font-family="{_FONT}"'
            f' font-size="{size}"{weight} fill="{color}"{fill_extra}{italic}>{content}</text>\n'
        )
        y += size + line_gap

    # Gradient: transparent → theme.background, covering bottom 55% of card
    grad_y_pct = "45%"
    defs = (
        f'<defs>'
        f'<clipPath id="bcc"><rect width="{w}" height="{h}" rx="10"/></clipPath>'
        f'<linearGradient id="bgrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="{grad_y_pct}" stop-color="{theme.background}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="{theme.background}" stop-opacity="1"/>'
        f'</linearGradient>'
        f'</defs>'
    )

    if data.cover_b64:
        cover_el = (
            f'  <image href="{data.cover_b64}" x="0" y="0" width="{w}" height="{h}"'
            f' clip-path="url(#bcc)" preserveAspectRatio="xMidYMid slice"/>\n'
        )
    else:
        # No cover — show accent-tinted top half, dark bottom
        cover_el = (
            f'  <rect width="{w}" height="{h // 2}" fill="{theme.accent}" opacity="0.25"/>\n'
            f'  <text x="{w // 2}" y="{h // 4 + 16}" font-size="48" text-anchor="middle"'
            f' font-family="serif" fill="{theme.text_secondary}">&#128214;</text>\n'
        )

    bar = _progress_bar(pad, h - 12, w - 2 * pad, data.progress, theme, show_pct=False)

    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  {defs}\n'
        f'  {_bg(w, h, theme)}\n'
        f'{cover_el}'
        f'  <rect width="{w}" height="{h}" clip-path="url(#bcc)" fill="url(#bgrad)"/>\n'
        f'{text_els}'
        f'  {bar}\n'
        f'</svg>'
    )


def render_portrait_b_demo(theme: Theme, label: Optional[str] = None) -> str:
    return render_portrait_b(theme, _DEMO_DATA, label=label or "Demo — configure credentials")


def render_portrait_b_nothing(theme: Theme) -> str:
    return _pt_status_card(theme, "No listening history yet")


def render_portrait_b_error(theme: Theme) -> str:
    return _pt_status_card(theme, "Unable to reach Audiobookshelf")


# ── Layout C — Frosted glass panel (240×360) ──────────────────────────────────
#
#  ┌──────────────────────────┐
#  │  [cover fills card,      │
#  │   blurred + darkened     │
#  │   via SVG filter]        │
#  │                          │
#  │ ╔════════════════════╗   │
#  │ ║ Currently Reading  ║   │ ← frosted panel
#  │ ║ Project Hail Mary  ║   │
#  │ ║ Andy Weir          ║   │
#  │ ║ Narrated by ...    ║   │
#  │ ╚════════════════════╝   │
#  │                          │
#  └──────────────────────────┘

def render_portrait_c(theme: Theme, data: CardData, label: str = "Currently Reading") -> str:
    w, h   = _PT_W, _PT_H
    pad    = _PT_PAD
    p_pad  = 12    # panel internal padding
    p_x    = pad
    p_w    = w - 2 * pad
    p_rx   = 8

    title  = _x(_trunc(data.title,  22))
    author = _x(_trunc(data.author, 24))
    lines: list[tuple[int, bool, str, bool]] = [
        (10, False, _x(label),  False),
        (14, True,  title,      False),
        (12, False, author,     False),
    ]
    if data.narrator:
        lines.append((11, False, f'Narrated by {_x(_trunc(data.narrator, 20))}', False))
    pubyr_parts = [p for p in [data.publisher, data.year] if p]
    if pubyr_parts:
        lines.append((11, False, _x(_trunc(" · ".join(pubyr_parts), 26)), False))
    if data.series:
        lines.append((11, False, _x(_trunc(data.series, 26)), False))
    else:
        lines.append((11, False, "Standalone", True))

    line_gap = 7
    block_h = sum(s + line_gap for s, _, _, _ in lines) + p_pad
    p_h  = block_h + p_pad
    p_y  = h - pad - p_h

    text_els = ""
    y = p_y + p_pad + lines[0][0]
    for size, bold, content, muted in lines:
        weight  = ' font-weight="600"' if bold else ""
        color   = theme.text_primary if bold else theme.text_secondary
        opacity = ' opacity="0.45" font-style="italic"' if muted else ""
        text_els += (
            f'  <text x="{p_x + p_pad}" y="{y}" font-family="{_FONT}"'
            f' font-size="{size}"{weight} fill="{color}"{opacity}>{content}</text>\n'
        )
        y += size + line_gap

    defs = (
        f'<defs>'
        f'<clipPath id="ccc"><rect width="{w}" height="{h}" rx="10"/></clipPath>'
        f'<filter id="cblur" x="-10%" y="-10%" width="120%" height="120%">'
        f'<feGaussianBlur stdDeviation="8"/>'
        f'</filter>'
        f'</defs>'
    )

    if data.cover_b64:
        cover_el = (
            f'  <image href="{data.cover_b64}" x="0" y="0" width="{w}" height="{h}"'
            f' clip-path="url(#ccc)" preserveAspectRatio="xMidYMid slice"'
            f' filter="url(#cblur)"/>\n'
            f'  <rect width="{w}" height="{h}" clip-path="url(#ccc)"'
            f' fill="{theme.background}" opacity="0.45"/>\n'
        )
    else:
        cover_el = (
            f'  <rect width="{w}" height="{h}" fill="{theme.background}"/>\n'
            f'  <text x="{w // 2}" y="{p_y // 2 + 16}" font-size="56" text-anchor="middle"'
            f' font-family="serif" fill="{theme.border}">&#128214;</text>\n'
        )

    panel = (
        f'  <rect x="{p_x}" y="{p_y}" width="{p_w}" height="{p_h}" rx="{p_rx}"'
        f' fill="{theme.background}" opacity="0.88"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
    )

    bar = _progress_bar(pad, h - 12, w - 2 * pad, data.progress, theme, show_pct=False)

    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  {defs}\n'
        f'  {_bg(w, h, theme)}\n'
        f'{cover_el}'
        f'{panel}'
        f'{text_els}'
        f'  {bar}\n'
        f'</svg>'
    )


def render_portrait_c_demo(theme: Theme, label: Optional[str] = None) -> str:
    return render_portrait_c(theme, _DEMO_DATA, label=label or "Demo — configure credentials")


def render_portrait_c_nothing(theme: Theme) -> str:
    return _pt_status_card(theme, "No listening history yet")


def render_portrait_c_error(theme: Theme) -> str:
    return _pt_status_card(theme, "Unable to reach Audiobookshelf")


# ── Layout D — Sidebar accent stripe (240×360) ────────────────────────────────
#
#  ┌─┬──────────────────────┐
#  │█│ [cover 100×100]      │
#  │█│                      │
#  │█├──────────────────────┤
#  │█│ Currently Reading    │
#  │█│ Project Hail Mary    │
#  │ │ Andy Weir            │
#  │ │ Narrated by ...      │
#  │ │ Publisher · Year     │
#  │ │ Series               │
#  └─┴──────────────────────┘

_D_STRIPE_W = 6

def render_portrait_d(theme: Theme, data: CardData, label: str = "Currently Reading") -> str:
    w, h      = _PT_W, _PT_H
    pad       = _PT_PAD
    sw        = _D_STRIPE_W
    content_x = sw + pad          # text/cover start x

    # Cover thumbnail — square, fits in content column
    thumb_size = 100
    thumb_x    = content_x
    thumb_y    = pad
    text_x     = content_x
    div_y      = thumb_y + thumb_size + 10

    title  = _x(_trunc(data.title,  24))
    author = _x(_trunc(data.author, 26))
    lines: list[tuple[int, bool, str, bool]] = [
        (10, False, _x(label),  False),
        (14, True,  title,      False),
        (12, False, author,     False),
    ]
    if data.narrator:
        lines.append((11, False, f'Narrated by {_x(_trunc(data.narrator, 22))}', False))
    pubyr_parts = [p for p in [data.publisher, data.year] if p]
    if pubyr_parts:
        lines.append((11, False, _x(_trunc(" · ".join(pubyr_parts), 26)), False))
    if data.series:
        lines.append((11, False, _x(_trunc(data.series, 26)), False))
    else:
        lines.append((11, False, "Standalone", True))

    line_gap  = 7
    y = div_y + 18
    text_els  = ""
    for size, bold, content, muted in lines:
        weight  = ' font-weight="600"' if bold else ""
        color   = theme.text_primary if bold else theme.text_secondary
        opacity = ' opacity="0.45" font-style="italic"' if muted else ""
        text_els += (
            f'  <text x="{text_x}" y="{y}" font-family="{_FONT}"'
            f' font-size="{size}"{weight} fill="{color}"{opacity}>{content}</text>\n'
        )
        y += size + line_gap

    # Stripe height covers label + title + author rows, then fades
    stripe_full_h = div_y + (10 + lines[0][0] + line_gap + lines[1][0] + line_gap + lines[2][0])

    defs = (
        f'<defs>'
        f'<clipPath id="dcc"><rect width="{w}" height="{h}" rx="10"/></clipPath>'
        f'<clipPath id="dthumb"><rect x="{thumb_x}" y="{thumb_y}" width="{thumb_size}" height="{thumb_size}" rx="6"/></clipPath>'
        f'<linearGradient id="dstripe" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{theme.accent}"/>'
        f'<stop offset="70%" stop-color="{theme.accent}"/>'
        f'<stop offset="100%" stop-color="{theme.accent}" stop-opacity="0"/>'
        f'</linearGradient>'
        f'</defs>'
    )

    divider = (
        f'  <line x1="{content_x}" y1="{div_y}" x2="{w - pad}" y2="{div_y}"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
    )

    if data.cover_b64:
        thumb_el = (
            f'  <image href="{data.cover_b64}" x="{thumb_x}" y="{thumb_y}"'
            f' width="{thumb_size}" height="{thumb_size}"'
            f' clip-path="url(#dthumb)" preserveAspectRatio="xMidYMid slice"/>\n'
        )
    else:
        mid_x = thumb_x + thumb_size // 2
        mid_y = thumb_y + thumb_size // 2
        thumb_el = (
            f'  <rect x="{thumb_x}" y="{thumb_y}" width="{thumb_size}" height="{thumb_size}"'
            f' rx="6" fill="{theme.border}"/>\n'
            f'  <text x="{mid_x}" y="{mid_y + 12}" font-size="28" text-anchor="middle"'
            f' font-family="serif" fill="{theme.text_secondary}">&#128214;</text>\n'
        )

    bar = _progress_bar(pad, h - 12, w - 2 * pad, data.progress, theme, show_pct=False)

    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  {defs}\n'
        f'  {_bg(w, h, theme)}\n'
        f'  <rect x="0" y="0" width="{sw}" height="{h}" rx="0" clip-path="url(#dcc)"'
        f' fill="url(#dstripe)"/>\n'
        f'{thumb_el}'
        f'{divider}'
        f'{text_els}'
        f'  {bar}\n'
        f'</svg>'
    )


def render_portrait_d_demo(theme: Theme, label: Optional[str] = None) -> str:
    return render_portrait_d(theme, _DEMO_DATA, label=label or "Demo — configure credentials")


def render_portrait_d_nothing(theme: Theme) -> str:
    return _pt_status_card(theme, "No listening history yet")


def render_portrait_d_error(theme: Theme) -> str:
    return _pt_status_card(theme, "Unable to reach Audiobookshelf")


# ── Layout E — Editorial / typographic (240×360) ─────────────────────────────
#
#  ┌──────────────────────────┐
#  │ CURRENTLY READING        │ ← spaced label
#  │                          │
#  │ ┌──────┐  Andy Weir      │
#  │ │ 80×80│  2021           │ ← small thumbnail + quick-meta
#  │ └──────┘                 │
#  │                          │
#  │ Project                  │ ← large wrapped title
#  │ Hail Mary                │
#  │                          │
#  │ ───────────────────────  │ ← rule
#  │                          │
#  │ Narrated by              │
#  │ Ray Porter               │
#  │                          │
#  │ Ballantine Books         │
#  │ The Weir Trilogy · Bk 2  │
#  └──────────────────────────┘

def _word_wrap(text: str, max_chars: int) -> list[str]:
    """Greedy word-wrap for monospace fonts."""
    words  = text.split()
    lines  = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def render_portrait_e(theme: Theme, data: CardData, label: str = "Currently Reading") -> str:
    w, h  = _PT_W, _PT_H
    pad   = _PT_PAD

    thumb = 80
    thumb_x, thumb_y = pad, 44

    # Quick-meta beside thumbnail: author + year (compact)
    meta_x   = thumb_x + thumb + 10
    author_s = _x(_trunc(data.author, 12))
    year_s   = _x(data.year or "")

    # Large wrapped title — monospace ~17 chars per line at 18px in 208px
    title_lines = _word_wrap(data.title, 17)
    title_y_start = thumb_y + thumb + 22
    title_line_h  = 24

    rule_y = title_y_start + len(title_lines) * title_line_h + 10

    # Lower detail lines
    detail_lines: list[tuple[str, bool]] = []
    if data.narrator:
        detail_lines.append((f'Narrated by {_x(_trunc(data.narrator, 22))}', False))
    pubyr_parts = [p for p in [data.publisher, data.year] if p]
    if pubyr_parts:
        detail_lines.append((_x(_trunc(" · ".join(pubyr_parts), 26)), False))
    if data.series:
        detail_lines.append((_x(_trunc(data.series, 26)), False))
    else:
        detail_lines.append(("Standalone", True))

    detail_y  = rule_y + 18
    detail_els = ""
    for content, muted in detail_lines:
        opacity = ' opacity="0.45" font-style="italic"' if muted else ""
        detail_els += (
            f'  <text x="{pad}" y="{detail_y}" font-family="{_FONT}"'
            f' font-size="11" fill="{theme.text_secondary}"{opacity}>{content}</text>\n'
        )
        detail_y += 18

    if data.cover_b64:
        thumb_el = (
            f'<defs><clipPath id="eth"><rect x="{thumb_x}" y="{thumb_y}"'
            f' width="{thumb}" height="{thumb}" rx="5"/></clipPath></defs>'
            f'  <image href="{data.cover_b64}" x="{thumb_x}" y="{thumb_y}"'
            f' width="{thumb}" height="{thumb}"'
            f' clip-path="url(#eth)" preserveAspectRatio="xMidYMid slice"/>\n'
        )
    else:
        mid_x = thumb_x + thumb // 2
        mid_y = thumb_y + thumb // 2
        thumb_el = (
            f'  <rect x="{thumb_x}" y="{thumb_y}" width="{thumb}" height="{thumb}"'
            f' rx="5" fill="{theme.border}"/>\n'
            f'  <text x="{mid_x}" y="{mid_y + 10}" font-size="24" text-anchor="middle"'
            f' font-family="serif" fill="{theme.text_secondary}">&#128214;</text>\n'
        )

    title_els = "".join(
        f'  <text x="{pad}" y="{title_y_start + i * title_line_h}"'
        f' font-family="{_FONT}" font-size="18" font-weight="700"'
        f' fill="{theme.text_primary}">{_x(line)}</text>\n'
        for i, line in enumerate(title_lines)
    )

    rule = (
        f'  <line x1="{pad}" y1="{rule_y}" x2="{w - pad}" y2="{rule_y}"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
    )

    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  {_bg(w, h, theme)}\n'
        f'  <text x="{pad}" y="28" font-family="{_FONT}" font-size="9"'
        f' fill="{theme.accent}" letter-spacing="2">{_x(label.upper())}</text>\n'
        f'{thumb_el}'
        f'  <text x="{meta_x}" y="{thumb_y + 18}" font-family="{_FONT}"'
        f' font-size="12" font-weight="600" fill="{theme.text_primary}">{author_s}</text>\n'
        f'  <text x="{meta_x}" y="{thumb_y + 36}" font-family="{_FONT}"'
        f' font-size="11" fill="{theme.text_secondary}">{year_s}</text>\n'
        f'{title_els}'
        f'{rule}'
        f'{detail_els}'
        f'  {_progress_bar(pad, h - 12, w - 2 * pad, data.progress, theme, show_pct=False)}\n'
        f'</svg>'
    )


def render_portrait_e_demo(theme: Theme, label: Optional[str] = None) -> str:
    return render_portrait_e(theme, _DEMO_DATA, label=label or "Currently Reading")


def render_portrait_e_nothing(theme: Theme) -> str:
    return _pt_status_card(theme, "No listening history yet")


def render_portrait_e_error(theme: Theme) -> str:
    return _pt_status_card(theme, "Unable to reach Audiobookshelf")


# ── Layout F — Slim Bookmark (150×460) ───────────────────────────────────────
#
#  ┌─────────────┐
#  │      ●      │  ← decorative hole
#  │  ┌───────┐  │
#  │  │ cover │  │
#  │  └───────┘  │
#  ├─────────────┤
#  │ Currently   │
#  │ Reading     │
#  │ Project     │
#  │ Hail Mary   │
#  │ Andy Weir   │
#  │ ██████░     │
#  │             │
#  └──────┬──────┘
#          ▼  V-notch

_PF_W        = 150
_PF_H        = 460
_PF_NOTCH    = 26
_PF_PAD      = 14
_PF_COVER_SZ = 120
_PF_RX       = 10
_PF_HOLE_R   = 6


def _pf_bm_path(w: int, h: int, notch: int, rx: int) -> str:
    return (
        f'M {rx},0 L {w-rx},0 Q {w},0 {w},{rx} '
        f'L {w},{h-notch} L {w//2},{h} L 0,{h-notch} '
        f'L 0,{rx} Q 0,0 {rx},0 Z'
    )


def _pf_status_card(theme: Theme, message: str) -> str:
    w, h = _PF_W, _PF_H
    p = _pf_bm_path(w, h, _PF_NOTCH, _PF_RX)
    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <path d="{p}" fill="{theme.background}" stroke="{theme.border}" stroke-width="1"/>\n'
        f'  <text x="{w//2}" y="{h//2}" font-family="{_FONT}" font-size="10"'
        f' fill="{theme.text_secondary}" text-anchor="middle">{_x(message)}</text>\n'
        f'</svg>'
    )


def render_portrait_f(theme: Theme, data: CardData, label: str = "Currently Reading") -> str:
    w, h    = _PF_W, _PF_H
    pad     = _PF_PAD
    notch   = _PF_NOTCH
    cov_sz  = _PF_COVER_SZ

    bm_path = _pf_bm_path(w, h, notch, _PF_RX)

    hole_cx = w // 2
    hole_cy = 18
    cov_x   = pad
    cov_y   = hole_cy + _PF_HOLE_R + 8   # 32
    div_y   = cov_y + cov_sz + 8         # 160

    title_lines = _word_wrap(data.title, 14)[:2]
    lines: list[tuple[int, bool, str]] = [(9, False, _x(label))]
    for tl in title_lines:
        lines.append((13, True, _x(tl)))
    lines.append((11, False, _x(_trunc(data.author, 16))))
    if data.narrator:
        lines.append((10, False, _x(_trunc(data.narrator, 17))))
    pubyr_parts = [p for p in [data.publisher, data.year] if p]
    if pubyr_parts:
        lines.append((10, False, _x(_trunc(" · ".join(pubyr_parts), 17))))
    if data.series:
        lines.append((10, False, _x(_trunc(data.series, 17))))

    y = div_y + 16
    text_els = ""
    for size, bold, content in lines:
        weight = ' font-weight="600"' if bold else ""
        color  = theme.text_primary if bold else theme.text_secondary
        text_els += (
            f'  <text x="{pad}" y="{y}" font-family="{_FONT}"'
            f' font-size="{size}"{weight} fill="{color}">{content}</text>\n'
        )
        y += size + 5

    bar_y = h - notch - 20
    bar   = _progress_bar(pad, bar_y, w - 2 * pad, data.progress, theme, show_pct=False)

    divider = (
        f'  <line x1="{pad}" y1="{div_y}" x2="{w - pad}" y2="{div_y}"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
    )

    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  <path d="{bm_path}" fill="{theme.background}"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
        f'  {_cover(cov_x, cov_y, cov_sz, cov_sz, data.cover_b64, theme, clip_id="fcc")}\n'
        f'{divider}'
        f'{text_els}'
        f'  <circle cx="{hole_cx}" cy="{hole_cy}" r="{_PF_HOLE_R}"'
        f' fill="{theme.background}" stroke="{theme.border}" stroke-width="1.5"/>\n'
        f'  {bar}\n'
        f'</svg>'
    )


def render_portrait_f_demo(theme: Theme, label: Optional[str] = None) -> str:
    return render_portrait_f(theme, _DEMO_DATA, label=label or "Currently Reading")


def render_portrait_f_nothing(theme: Theme) -> str:
    return _pf_status_card(theme, "No listening history yet")


def render_portrait_f_error(theme: Theme) -> str:
    return _pf_status_card(theme, "Unable to reach Audiobookshelf")


# ── Layout G — Dog-ear Corner (220×300) ──────────────────────────────────────
#
#  ┌──────────────────────────────────┐
#  │ [cover ]  Currently Reading      │
#  │  80×80    Project Hail Mary      │
#  │           Andy Weir              │
#  ├──────────────────────────────────┤
#  │ Narrated by Ray Porter           │
#  │ Ballantine Books · 2021          │
#  │ The Weir Trilogy · Book 2        │
#  │                                  │
#  │ ████████████████░░░              │
#  │                                  │
#  └──────────────────────────────────/
#                                    \  ← folded corner

_PG_W    = 220
_PG_H    = 300
_PG_FOLD = 40
_PG_PAD  = 16
_PG_RX   = 10


def _pg_card_path(w: int, h: int, fold: int, rx: int) -> str:
    return (
        f'M {rx},0 L {w-rx},0 Q {w},0 {w},{rx} '
        f'L {w},{h-fold} L {w-fold},{h} '
        f'L {rx},{h} Q 0,{h} 0,{h-rx} '
        f'L 0,{rx} Q 0,0 {rx},0 Z'
    )


def _pg_flap_path(w: int, h: int, fold: int) -> str:
    return f'M {w},{h-fold} L {w-fold},{h} L {w},{h} Z'


def _pg_status_card(theme: Theme, message: str) -> str:
    w, h = _PG_W, _PG_H
    cp = _pg_card_path(w, h, _PG_FOLD, _PG_RX)
    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <path d="{cp}" fill="{theme.background}" stroke="{theme.border}" stroke-width="1"/>\n'
        f'  <path d="{_pg_flap_path(w, h, _PG_FOLD)}" fill="{theme.border}" opacity="0.7"/>\n'
        f'  <text x="{w//2}" y="{h//2}" font-family="{_FONT}" font-size="11"'
        f' fill="{theme.text_secondary}" text-anchor="middle">{_x(message)}</text>\n'
        f'</svg>'
    )


def render_portrait_g(theme: Theme, data: CardData, label: str = "Currently Reading") -> str:
    w, h  = _PG_W, _PG_H
    pad   = _PG_PAD
    fold  = _PG_FOLD

    card_path = _pg_card_path(w, h, fold, _PG_RX)
    flap_path = _pg_flap_path(w, h, fold)

    cov_sz = 80
    cov_x, cov_y = pad, pad

    txt_x   = cov_x + cov_sz + 10    # 106
    txt_w   = w - txt_x - pad        # 98 — chars ≈ 11 at 9px, 9 at 12px

    title_lines = _word_wrap(data.title, 10)[:2]

    y_label  = cov_y + 14
    y_title1 = y_label + 9 + 4
    y_title2 = y_title1 + 12 + 3
    has_t2   = len(title_lines) > 1
    y_author = (y_title2 if has_t2 else y_title1) + 12 + 4

    div_y = cov_y + cov_sz + 10      # 106

    below_lines: list[str] = []
    if data.narrator:
        below_lines.append(_x(_trunc(data.narrator, 26)))
    pubyr_parts = [p for p in [data.publisher, data.year] if p]
    if pubyr_parts:
        below_lines.append(_x(_trunc(" · ".join(pubyr_parts), 26)))
    if data.series:
        below_lines.append(_x(_trunc(data.series, 26)))

    y = div_y + 16
    below_els = ""
    for content in below_lines:
        below_els += (
            f'  <text x="{pad}" y="{y}" font-family="{_FONT}"'
            f' font-size="10" fill="{theme.text_secondary}">{content}</text>\n'
        )
        y += 15

    bar_y = h - fold - 20            # 240 — safely above the fold diagonal
    bar   = _progress_bar(pad, bar_y, w - 2 * pad, data.progress, theme, show_pct=False)

    divider = (
        f'  <line x1="{pad}" y1="{div_y}" x2="{w - pad - fold // 2}" y2="{div_y}"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
    )

    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg"'
        f' xmlns:xlink="http://www.w3.org/1999/xlink">\n'
        f'  <path d="{card_path}" fill="{theme.background}"'
        f' stroke="{theme.border}" stroke-width="1"/>\n'
        f'  <path d="{flap_path}" fill="{theme.border}" opacity="0.7"/>\n'
        f'  {_cover(cov_x, cov_y, cov_sz, cov_sz, data.cover_b64, theme, clip_id="gcc")}\n'
        f'  <text x="{txt_x}" y="{y_label}" font-family="{_FONT}"'
        f' font-size="9" fill="{theme.text_secondary}">{_x(label)}</text>\n'
        f'  <text x="{txt_x}" y="{y_title1}" font-family="{_FONT}"'
        f' font-size="12" font-weight="600" fill="{theme.text_primary}">'
        f'{_x(title_lines[0])}</text>\n'
        + (
            f'  <text x="{txt_x}" y="{y_title2}" font-family="{_FONT}"'
            f' font-size="12" font-weight="600" fill="{theme.text_primary}">'
            f'{_x(title_lines[1])}</text>\n'
            if has_t2 else ""
        ) +
        f'  <text x="{txt_x}" y="{y_author}" font-family="{_FONT}"'
        f' font-size="10" fill="{theme.text_secondary}">'
        f'{_x(_trunc(data.author, 11))}</text>\n'
        f'{divider}'
        f'{below_els}'
        f'  {bar}\n'
        f'</svg>'
    )


def render_portrait_g_demo(theme: Theme, label: Optional[str] = None) -> str:
    return render_portrait_g(theme, _DEMO_DATA, label=label or "Currently Reading")


def render_portrait_g_nothing(theme: Theme) -> str:
    return _pg_status_card(theme, "No listening history yet")


def render_portrait_g_error(theme: Theme) -> str:
    return _pg_status_card(theme, "Unable to reach Audiobookshelf")

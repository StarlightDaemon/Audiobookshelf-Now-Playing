import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .abs import AbsClient, is_configured
from .cache import TTLCache
from .config import AppConfig, load_config, save_config
from .render import (
    CardData,
    render_landscape, render_landscape_demo, render_landscape_standalone_demo,
    render_landscape_error, render_landscape_nothing_playing,
    render_portrait, render_portrait_demo, render_portrait_error, render_portrait_nothing_playing,
    render_portrait_b, render_portrait_b_demo, render_portrait_b_nothing, render_portrait_b_error,
    render_portrait_c, render_portrait_c_demo, render_portrait_c_nothing, render_portrait_c_error,
    render_portrait_d, render_portrait_d_demo, render_portrait_d_nothing, render_portrait_d_error,
    render_portrait_e, render_portrait_e_demo, render_portrait_e_nothing, render_portrait_e_error,
    render_portrait_f, render_portrait_f_demo, render_portrait_f_nothing, render_portrait_f_error,
    render_portrait_g, render_portrait_g_demo, render_portrait_g_nothing, render_portrait_g_error,
)
from .settings_ui import build_settings_page
from .themes import DEFAULT_THEME, THEMES

logger = logging.getLogger(__name__)

# How often to poll ABS for the current session (book changes only)
SESSION_TTL = int(os.environ.get("SESSION_TTL", "300"))
# How long to cache metadata + cover art per book (expensive; only re-fetched on book change)
CARD_TTL = int(os.environ.get("CARD_TTL", "300"))

_session_cache: TTLCache   # short — current session info
_card_cache: TTLCache      # long — metadata + cover keyed by item_id
_abs: Optional[AbsClient]
_configured: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _session_cache, _card_cache, _abs, _configured
    _configured = is_configured()
    _session_cache = TTLCache(ttl=SESSION_TTL)
    _card_cache = TTLCache(ttl=CARD_TTL)
    _abs = AbsClient() if _configured else None
    if not _configured:
        logger.warning(
            "ABS credentials not configured — serving demo card. "
            "Set ABS_HOST and ABS_TOKEN in /etc/audiobookshelf-now-playing.env "
            "then restart the service."
        )
    yield
    if _abs is not None:
        await _abs.aclose()


app = FastAPI(title="Audiobookshelf Now Playing", lifespan=lifespan)


async def _fetch_card_data() -> Optional[CardData]:
    """
    Two-tier fetch:
    - Session (SESSION_TTL): poll — detects book changes.
    - Card metadata (CARD_TTL, keyed by item_id): cover art + title/author/series.
      Only re-fetched when the book changes or CARD_TTL expires.
    """
    # ── Session (short cache) ─────────────────────────────────────────────────
    session = _session_cache.get("session")
    if session is None:
        session = await _abs.get_current_session()
        _session_cache.set("session", session if session is not None else False)
    elif session is False:
        session = None

    if session is None:
        return None

    item_id: str = session.get("libraryItemId", "")

    # ── Card metadata (long cache, keyed by item_id) ──────────────────────────
    # A different item_id is a natural cache miss — no manual invalidation needed.
    meta = _card_cache.get(item_id)
    if meta is None:
        item = await _abs.get_item(item_id)
        item_meta = item.get("media", {}).get("metadata", {})

        title = item_meta.get("title") or "Unknown Title"
        author = item_meta.get("authorName") or ", ".join(
            a["name"] for a in item_meta.get("authors", []) if a.get("name")
        ) or "Unknown Author"

        series: Optional[str] = None
        for s in item_meta.get("series", []):
            name = s.get("name", "")
            seq = s.get("sequence", "")
            series = f"{name} · Book {seq}" if seq else name
            break

        narrator: Optional[str] = item_meta.get("narrator") or None
        if not narrator:
            parts = []
            for n in item_meta.get("narrators", []):
                if isinstance(n, str) and n:
                    parts.append(n)
                elif isinstance(n, dict) and n.get("name"):
                    parts.append(n["name"])
            narrator = ", ".join(parts) or None

        publisher: Optional[str] = item_meta.get("publisher") or None

        raw_year = item_meta.get("publishedYear")
        year: Optional[str] = str(raw_year) if raw_year else None

        try:
            cover_b64 = await _abs.get_cover_b64(item_id)
        except Exception:
            cover_b64 = None

        meta = {
            "title": title, "author": author, "series": series, "cover_b64": cover_b64,
            "narrator": narrator, "publisher": publisher, "year": year,
        }
        _card_cache.set(item_id, meta)

    ct  = session.get("currentTime") or 0
    dur = session.get("duration") or 0
    progress = ct / dur if dur > 0 else None

    return CardData(
        title=meta["title"],
        author=meta["author"],
        series=meta["series"],
        cover_b64=meta["cover_b64"],
        narrator=meta["narrator"],
        publisher=meta["publisher"],
        year=meta["year"],
        progress=progress,
    )


async def _serve_card(render_fn, demo_fn, nothing_fn, error_fn, theme_key: str,
                      cache_max_age: Optional[int] = None,
                      label: Optional[str] = None,
                      corners: str = "rounded") -> Response:
    t = THEMES.get(theme_key, THEMES[DEFAULT_THEME])
    if not _configured:
        svg = demo_fn(t, label=label, corners=corners)
        return Response(content=svg, media_type="image/svg+xml",
                        headers={"Cache-Control": "no-store"})
    try:
        data = await _fetch_card_data()
        if data is None:
            svg = nothing_fn(t)
        else:
            kwargs: dict = {"corners": corners}
            if label is not None:
                kwargs["label"] = label
            svg = render_fn(t, data, **kwargs)
    except Exception:
        logger.exception("Failed to fetch card data from ABS")
        svg = error_fn(t)
    max_age = cache_max_age if cache_max_age is not None else SESSION_TTL
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": f"public, max-age={max_age}"})


@app.get("/cardlandscape")
async def card_landscape_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    return await _serve_card(
        render_landscape, render_landscape_demo,
        render_landscape_nothing_playing, render_landscape_error,
        theme,
    )


@app.get("/cardportrait")
async def card_portrait_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    return await _serve_card(
        render_portrait, render_portrait_demo,
        render_portrait_nothing_playing, render_portrait_error,
        theme,
    )


@app.get("/cardlandscapedemo")
async def card_landscape_demo_endpoint(theme: str = Query(default=DEFAULT_THEME),
                                       label: Optional[str] = Query(default=None),
                                       corners: str = Query(default="rounded")):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return Response(content=render_landscape_demo(t, label=label, corners=corners),
                    media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.get("/cardlandscapestandalonedemo")
async def card_landscape_standalone_demo_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return Response(content=render_landscape_standalone_demo(t), media_type="image/svg+xml",
                    headers={"Cache-Control": "no-store"})


# ── Portrait layout variants ──────────────────────────────────────────────────

@app.get("/cardportraitb")
async def card_portrait_b_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    return await _serve_card(
        render_portrait_b, render_portrait_b_demo,
        render_portrait_b_nothing, render_portrait_b_error, theme,
    )

@app.get("/cardportraitbdemo")
async def card_portrait_b_demo_endpoint(theme: str = Query(default=DEFAULT_THEME),
                                        label: Optional[str] = Query(default=None),
                                        corners: str = Query(default="rounded")):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return Response(content=render_portrait_b_demo(t, label=label, corners=corners),
                    media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.get("/cardportraitc")
async def card_portrait_c_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    return await _serve_card(
        render_portrait_c, render_portrait_c_demo,
        render_portrait_c_nothing, render_portrait_c_error, theme,
    )

@app.get("/cardportraitcdemo")
async def card_portrait_c_demo_endpoint(theme: str = Query(default=DEFAULT_THEME),
                                        label: Optional[str] = Query(default=None),
                                        corners: str = Query(default="rounded")):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return Response(content=render_portrait_c_demo(t, label=label, corners=corners),
                    media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.get("/cardportraitd")
async def card_portrait_d_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    return await _serve_card(
        render_portrait_d, render_portrait_d_demo,
        render_portrait_d_nothing, render_portrait_d_error, theme,
    )

@app.get("/cardportraitddemo")
async def card_portrait_d_demo_endpoint(theme: str = Query(default=DEFAULT_THEME),
                                        label: Optional[str] = Query(default=None),
                                        corners: str = Query(default="rounded")):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return Response(content=render_portrait_d_demo(t, label=label, corners=corners),
                    media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.get("/cardportraite")
async def card_portrait_e_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    return await _serve_card(
        render_portrait_e, render_portrait_e_demo,
        render_portrait_e_nothing, render_portrait_e_error, theme,
    )

@app.get("/cardportraitedemo")
async def card_portrait_e_demo_endpoint(theme: str = Query(default=DEFAULT_THEME),
                                        label: Optional[str] = Query(default=None),
                                        corners: str = Query(default="rounded")):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return Response(content=render_portrait_e_demo(t, label=label, corners=corners),
                    media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.get("/cardportraitf")
async def card_portrait_f_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    return await _serve_card(
        render_portrait_f, render_portrait_f_demo,
        render_portrait_f_nothing, render_portrait_f_error, theme,
    )

@app.get("/cardportraitfdemo")
async def card_portrait_f_demo_endpoint(theme: str = Query(default=DEFAULT_THEME),
                                        label: Optional[str] = Query(default=None),
                                        corners: str = Query(default="rounded")):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return Response(content=render_portrait_f_demo(t, label=label, corners=corners),
                    media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.get("/cardportraitg")
async def card_portrait_g_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    return await _serve_card(
        render_portrait_g, render_portrait_g_demo,
        render_portrait_g_nothing, render_portrait_g_error, theme,
    )

@app.get("/cardportraitgdemo")
async def card_portrait_g_demo_endpoint(theme: str = Query(default=DEFAULT_THEME),
                                        label: Optional[str] = Query(default=None),
                                        corners: str = Query(default="rounded")):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return Response(content=render_portrait_g_demo(t, label=label, corners=corners),
                    media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.get("/cardportraitdemo")
async def card_portrait_demo_endpoint(theme: str = Query(default=DEFAULT_THEME),
                                      label: Optional[str] = Query(default=None),
                                      corners: str = Query(default="rounded")):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    return Response(content=render_portrait_demo(t, label=label, corners=corners),
                    media_type="image/svg+xml", headers={"Cache-Control": "no-store"})


@app.get("/health")
async def health():
    return {"status": "ok", "demo_mode": not _configured}


@app.get("/status")
async def status():
    if not _configured:
        return {"playing": False, "demo_mode": True}
    try:
        data = await _fetch_card_data()
        if data is None:
            return {"playing": False, "demo_mode": False}
        return {
            "playing": True,
            "demo_mode": False,
            "title": data.title,
            "author": data.author,
            "series": data.series,
        }
    except Exception:
        return {"playing": False, "error": True}


# ── Settings UI ───────────────────────────────────────────────────────────────

_LAYOUT_MAP = {
    "landscape":  (render_landscape,  render_landscape_demo,  render_landscape_nothing_playing, render_landscape_error),
    "portrait":   (render_portrait,   render_portrait_demo,   render_portrait_nothing_playing,  render_portrait_error),
    "portrait-b": (render_portrait_b, render_portrait_b_demo, render_portrait_b_nothing,        render_portrait_b_error),
    "portrait-c": (render_portrait_c, render_portrait_c_demo, render_portrait_c_nothing,        render_portrait_c_error),
    "portrait-d": (render_portrait_d, render_portrait_d_demo, render_portrait_d_nothing,        render_portrait_d_error),
    "portrait-e": (render_portrait_e, render_portrait_e_demo, render_portrait_e_nothing,        render_portrait_e_error),
    "portrait-f": (render_portrait_f, render_portrait_f_demo, render_portrait_f_nothing,        render_portrait_f_error),
    "portrait-g": (render_portrait_g, render_portrait_g_demo, render_portrait_g_nothing,        render_portrait_g_error),
}


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    cfg = load_config()
    base = str(request.base_url).rstrip("/")
    return HTMLResponse(content=build_settings_page(cfg, base_url=base))


@app.get("/api/config")
async def get_config():
    cfg = load_config()
    return {"layout": cfg.layout, "theme": cfg.theme, "label": cfg.label, "corners": cfg.corners}


@app.post("/api/config")
async def post_config(request: Request):
    body = await request.json()
    layout = body.get("layout", "landscape")
    theme = body.get("theme", "dark")
    label = body.get("label", "Currently Reading")
    corners = body.get("corners", "rounded")
    from .config import VALID_LAYOUTS, VALID_THEMES, VALID_CORNERS
    if layout not in VALID_LAYOUTS:
        return JSONResponse({"error": f"Unknown layout: {layout}"}, status_code=400)
    if theme not in VALID_THEMES:
        return JSONResponse({"error": f"Unknown theme: {theme}"}, status_code=400)
    if corners not in VALID_CORNERS:
        return JSONResponse({"error": f"Unknown corners: {corners}"}, status_code=400)
    if not isinstance(label, str) or not label.strip():
        label = "Currently Reading"
    cfg = AppConfig(layout=layout, theme=theme, label=label.strip(), corners=corners)
    save_config(cfg)
    return {"layout": cfg.layout, "theme": cfg.theme, "label": cfg.label,
            "corners": cfg.corners, "saved": True}


@app.get("/card")
async def card_default():
    """Primary embed endpoint — layout, theme, label, and corners come from saved config."""
    cfg = load_config()
    fns = _LAYOUT_MAP[cfg.layout]
    return await _serve_card(*fns, cfg.theme, cache_max_age=30, label=cfg.label,
                             corners=cfg.corners)

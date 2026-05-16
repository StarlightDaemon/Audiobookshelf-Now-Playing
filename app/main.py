import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import Response

from .abs import AbsClient, is_configured
from .cache import TTLCache
from .render import CardData, render_card, render_demo, render_error, render_nothing_playing
from .themes import DEFAULT_THEME, THEMES

logger = logging.getLogger(__name__)

# How often to poll ABS for the current session (detects book changes quickly)
SESSION_TTL = int(os.environ.get("SESSION_TTL", "10"))
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


app = FastAPI(title="Audiobookshelf Now Playing", lifespan=lifespan)


async def _fetch_card_data() -> Optional[CardData]:
    """
    Two-tier fetch:
    - Session (SESSION_TTL): lightweight poll — detects book changes fast.
    - Card metadata (CARD_TTL, keyed by item_id): cover art + title/author/series.
      Only re-fetched when the book changes or CARD_TTL expires.
    Progress is always taken from the fresh session result.
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
    duration: float = session.get("duration") or 0
    current_time: float = session.get("currentTime") or 0
    progress = max(0.0, min(1.0, current_time / duration)) if duration > 0 else 0.0

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

        try:
            cover_b64 = await _abs.get_cover_b64(item_id)
        except Exception:
            cover_b64 = None

        meta = {"title": title, "author": author, "series": series, "cover_b64": cover_b64}
        _card_cache.set(item_id, meta)

    return CardData(
        title=meta["title"],
        author=meta["author"],
        series=meta["series"],
        progress=progress,
        cover_b64=meta["cover_b64"],
    )


@app.get("/card")
async def card_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])

    if not _configured:
        return Response(
            content=render_demo(t),
            media_type="image/svg+xml",
            headers={"Cache-Control": "no-store"},
        )

    try:
        data = await _fetch_card_data()
        svg = render_nothing_playing(t) if data is None else render_card(t, data)
    except Exception:
        logger.exception("Failed to fetch card data from ABS")
        svg = render_error(t)

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": f"public, max-age={SESSION_TTL}"},
    )


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
            "progress_pct": round(data.progress * 100),
        }
    except Exception:
        return {"playing": False, "error": True}

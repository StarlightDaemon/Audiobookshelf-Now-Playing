import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import Response

from .abs import AbsClient
from .cache import TTLCache
from .render import CardData, render_card, render_error, render_nothing_playing
from .themes import DEFAULT_THEME, THEMES

logger = logging.getLogger(__name__)

CACHE_TTL = int(os.environ.get("CACHE_TTL", "60"))

# Sentinel stored in cache when ABS confirms nothing is playing
_NOTHING = object()

_cache: TTLCache
_abs: AbsClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cache, _abs
    _cache = TTLCache(ttl=CACHE_TTL)
    _abs = AbsClient()
    yield


app = FastAPI(title="Audiobookshelf Now Playing", lifespan=lifespan)


async def _fetch_card_data() -> Optional[CardData]:
    """Return CardData, or None when nothing is playing. Raises on ABS error."""
    cached = _cache.get("card_data")
    if cached is not None:
        return None if cached is _NOTHING else cached

    session = await _abs.get_current_session()
    if session is None:
        _cache.set("card_data", _NOTHING)
        return None

    item_id = session.get("libraryItemId", "")
    item = await _abs.get_item(item_id)

    meta = item.get("media", {}).get("metadata", {})
    title = meta.get("title") or "Unknown Title"
    author = meta.get("authorName") or "Unknown Author"

    series: Optional[str] = None
    for s in meta.get("series", []):
        name = s.get("name", "")
        seq = s.get("sequence", "")
        series = f"{name} · Book {seq}" if seq else name
        break

    duration = session.get("duration") or 0
    current_time = session.get("currentTime") or 0
    progress = max(0.0, min(1.0, current_time / duration)) if duration > 0 else 0.0

    try:
        cover_b64 = await _abs.get_cover_b64(item_id)
    except Exception:
        cover_b64 = None

    data = CardData(
        title=title,
        author=author,
        series=series,
        progress=progress,
        cover_b64=cover_b64,
    )
    _cache.set("card_data", data)
    return data


@app.get("/card")
async def card_endpoint(theme: str = Query(default=DEFAULT_THEME)):
    t = THEMES.get(theme, THEMES[DEFAULT_THEME])
    try:
        data = await _fetch_card_data()
        svg = render_nothing_playing(t) if data is None else render_card(t, data)
    except Exception:
        logger.exception("Failed to fetch card data from ABS")
        svg = render_error(t)

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": f"public, max-age={CACHE_TTL}"},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}

import base64
import os
from typing import Optional

import httpx

_PLACEHOLDER_TOKEN = "your-abs-api-token-here"


def is_configured() -> bool:
    """Return True only when real ABS credentials are present in the environment."""
    token = os.environ.get("ABS_TOKEN", "")
    host = os.environ.get("ABS_HOST", "")
    return bool(token) and token != _PLACEHOLDER_TOKEN and bool(host)


class AbsClient:
    def __init__(self) -> None:
        self._host = os.environ["ABS_HOST"].rstrip("/")
        self._headers = {"Authorization": f"Bearer {os.environ['ABS_TOKEN']}"}

    async def get_current_session(self) -> Optional[dict]:
        """Return the most recent book listening session, or None if none exist."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._host}/api/me/listening-sessions",
                headers=self._headers,
                params={"itemsPerPage": 5},
                timeout=10,
            )
            resp.raise_for_status()

        sessions = resp.json().get("sessions", [])
        # Filter to audiobooks only (exclude podcasts)
        book_sessions = [s for s in sessions if s.get("mediaType") == "book"]
        return book_sessions[0] if book_sessions else None

    async def get_item(self, item_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._host}/api/items/{item_id}",
                headers=self._headers,
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_cover_b64(self, item_id: str) -> Optional[str]:
        """Fetch cover art and return as a data URI, or None on failure."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self._host}/api/items/{item_id}/cover",
                headers=self._headers,
                timeout=10,
                follow_redirects=True,
            )
        if resp.status_code != 200:
            return None
        content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
        encoded = base64.b64encode(resp.content).decode("ascii")
        return f"data:{content_type};base64,{encoded}"

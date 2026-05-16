"""Notification adapters. Currently: Discord webhook (most common free choice)."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

log = logging.getLogger(__name__)


def discord(name: str, report: dict[str, Any]) -> bool:
    """Post a short summary line to a Discord webhook. Returns True on success."""
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return False
    meta = report.get("metadata", {})
    summary = (report.get("ai") or {}).get("summary", "No summary")
    content = (
        f"**{name}** — weekly report\n"
        f"Rating: {meta.get('rating', 'N/A')} "
        f"({meta.get('userRatingCount', 0)} reviews)\n"
        f"> {summary}"
    )
    try:
        r = requests.post(url, json={"content": content[:1900]}, timeout=15)
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        log.error("Discord webhook failed: %s", e)
        return False

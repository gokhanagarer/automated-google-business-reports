"""Google Places API (New) client — metadata + reviews fetch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

FIELDS = (
    "displayName,rating,userRatingCount,reviews,"
    "currentOpeningHours,websiteUri,formattedAddress"
)


def fetch_place_details(place_id: str, api_key: str, timeout: int = 30) -> dict[str, Any]:
    """Fetch a place's metadata and up to 5 most recent reviews."""
    url = f"https://places.googleapis.com/v1/places/{place_id}"
    headers = {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": FIELDS}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()


def load_fixture(fixture_path: Path | str) -> dict[str, Any]:
    """Load a recorded Places API response from disk. Used by the offline demo."""
    return json.loads(Path(fixture_path).read_text(encoding="utf-8"))

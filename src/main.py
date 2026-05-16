"""Orchestrator: fetch → summarize → write → notify, for every configured subject."""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from . import notify
from .places import fetch_place_details, load_fixture
from .summarize import summarize

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("gbp-reports")

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.json"
OUTPUT_DIR = ROOT / "reports"
FIXTURE_DIR = ROOT / "fixtures"


def slugify(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")


def write_report(name: str, report: dict) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    date_tag = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = OUTPUT_DIR / f"{date_tag}_{slugify(name)}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def process(name: str, place_id: str, tone: str, *, live: bool) -> dict:
    if live:
        api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
        if not api_key:
            raise SystemExit("LIVE=1 but GOOGLE_PLACES_API_KEY is not set")
        data = fetch_place_details(place_id, api_key)
    else:
        fixture_name = os.environ.get("DEMO_FIXTURE", "demo_place.json")
        data = load_fixture(FIXTURE_DIR / fixture_name)

    ai = summarize(name, data, tone)
    return {
        "subject": name,
        "place_id": place_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "rating": data.get("rating"),
            "userRatingCount": data.get("userRatingCount"),
            "website": data.get("websiteUri"),
            "address": data.get("formattedAddress"),
        },
        "reviews": data.get("reviews", []),
        "ai": ai,
    }


def main() -> int:
    live = os.environ.get("LIVE", "0") == "1"
    mode = "LIVE (Google Places API)" if live else "DEMO (bundled fixture)"
    log.info("=== Automated Reports — mode: %s ===", mode)

    if not CONFIG_FILE.exists():
        log.error("Missing config.json. Copy config.example.json and edit.")
        return 1

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    subjects = config.get("subjects", [])
    tone = config.get("tone", "professional and friendly")
    if not subjects:
        log.error("No subjects configured.")
        return 1

    for s in subjects:
        name, place_id = s["name"], s["place_id"]
        log.info("Processing: %s", name)
        try:
            report = process(name, place_id, tone, live=live)
            path = write_report(name, report)
            log.info("  saved → %s", path)
            if notify.discord(name, report):
                log.info("  Discord notified")
        except Exception:
            log.exception("  failed for %s", name)

    log.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

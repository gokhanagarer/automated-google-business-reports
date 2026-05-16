"""Offline summarizer tests — no API keys required."""

import json
from pathlib import Path

import pytest

from src.summarize import summarize, _offline_summary


@pytest.fixture
def demo_data():
    fixture = Path(__file__).resolve().parent.parent / "fixtures" / "demo_place.json"
    return json.loads(fixture.read_text(encoding="utf-8"))


def test_offline_summary_returns_expected_keys(demo_data):
    out = _offline_summary("Example Subject", demo_data)
    assert set(out) == {"summary", "responses", "engine"}
    assert out["engine"] == "offline-template"


def test_offline_summary_mentions_rating_and_count(demo_data):
    out = _offline_summary("Example Subject", demo_data)
    assert "4.3" in out["summary"]
    assert "187" in out["summary"]


def test_offline_summary_drafts_replies_only_for_negative_reviews(demo_data):
    out = _offline_summary("Example Subject", demo_data)
    # demo fixture has 2 reviews below 4 stars
    assert len(out["responses"]) == 2
    for r in out["responses"]:
        assert r["rating"] < 4


def test_summarize_falls_back_to_offline_without_groq_key(demo_data, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    out = summarize("Example Subject", demo_data)
    assert out["engine"] == "offline-template"

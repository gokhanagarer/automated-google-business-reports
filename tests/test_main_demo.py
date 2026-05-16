"""End-to-end demo run — no network, no API keys."""

import json
import os
from pathlib import Path


def test_demo_writes_report(monkeypatch, tmp_path):
    monkeypatch.delenv("LIVE", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

    # Run the orchestrator
    from src import main as m

    exit_code = m.main()
    assert exit_code == 0

    # A timestamped report file should exist in reports/
    reports_dir = Path(m.OUTPUT_DIR)
    files = list(reports_dir.glob("*_example_subject.json"))
    assert files, "expected at least one report file for 'Example Subject'"

    payload = json.loads(files[-1].read_text(encoding="utf-8"))
    assert payload["subject"] == "Example Subject"
    assert payload["ai"]["engine"] == "offline-template"
    assert isinstance(payload["reviews"], list)

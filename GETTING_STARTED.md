# Getting started

A step-by-step guide. Aim: have a real Google Places review report in your terminal within 10 minutes, and a working scheduled job within 30.

If anything fails, jump to [Troubleshooting](#troubleshooting).

---

## 0. Prerequisites

You need:
- **Python 3.10+** (`python3 --version` to check)
- **git** (`git --version`)
- A Unix-like shell (macOS Terminal, Linux, WSL on Windows)

That's it. The demo runs without API keys.

---

## 1. Clone and run the demo

```bash
git clone https://github.com/gokhanagarer/automated-google-business-reports.git
cd automated-google-business-reports
make demo
```

What just happened:
- `make demo` created a virtual environment in `.venv/`
- Installed `requests` and `python-dotenv`
- Loaded `fixtures/demo_place.json` (a recorded Places API response)
- Ran the offline summarizer (template, not LLM)
- Wrote a report to `reports/YYYY-MM-DD_example_subject.json`

Open the report file — you'll see metadata, reviews, a one-line summary, and reply drafts for sub-4-star reviews.

---

## 2. Switch to live data

### 2.1 Get a Google Places API key

1. Open https://console.cloud.google.com → create or pick a project
2. Enable **Places API (New)**: APIs & Services → Library → search "Places API (New)" → Enable
3. APIs & Services → Credentials → **Create Credentials → API key**
4. Copy the key

### 2.2 Find the `place_id` for each business

Visit https://developers.google.com/maps/documentation/places/web-service/place-id and paste the business name or address. Copy the resulting `ChIJ...` ID.

### 2.3 Configure

```bash
cp .env.example .env
# open .env and set:
#   GOOGLE_PLACES_API_KEY=AIzaSy...
#   LIVE=1
```

Edit `config.json` to list the places you actually want to track:

```json
{
  "subjects": [
    { "name": "Main Store",   "place_id": "ChIJabc..." },
    { "name": "Second Store", "place_id": "ChIJxyz..." }
  ],
  "tone": "professional and friendly"
}
```

Run it:

```bash
make demo
```

The reports in `reports/` now contain real review data.

---

## 3. Optional: add LLM-generated summaries (Groq, free)

1. Sign up at https://console.groq.com (free tier, no credit card)
2. Create an API key
3. Add to `.env`:
   ```
   GROQ_API_KEY=gsk_...
   ```
4. Install Groq locally:
   ```bash
   .venv/bin/pip install groq
   ```
5. Re-run. The `ai.engine` field in the report flips from `offline-template` to `groq:llama-3.3-70b`.

---

## 4. Optional: post results to Discord

1. In your Discord server → channel → ⚙️ Edit Channel → Integrations → Webhooks → New Webhook → Copy URL
2. Add to `.env`:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```
3. Re-run. Each subject's summary is posted as a single message.

---

## 5. Schedule it weekly

### macOS / Linux (cron)

```bash
# edit your crontab
crontab -e
# add this line — every Monday at 9 AM
0 9 * * MON cd /absolute/path/to/automated-google-business-reports && /usr/bin/make demo
```

### GitHub Actions

Create `.github/workflows/weekly.yml`:

```yaml
name: weekly reports
on:
  schedule:
    - cron: "0 9 * * MON"
  workflow_dispatch:
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - env:
          GOOGLE_PLACES_API_KEY: ${{ secrets.GOOGLE_PLACES_API_KEY }}
          GROQ_API_KEY:          ${{ secrets.GROQ_API_KEY }}
          DISCORD_WEBHOOK_URL:   ${{ secrets.DISCORD_WEBHOOK_URL }}
          LIVE: "1"
        run: python -m src.main
      - uses: actions/upload-artifact@v4
        with: { name: reports, path: reports/ }
```

Add the secrets at **Settings → Secrets and variables → Actions**.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `make: command not found` | `make` isn't installed | macOS: `xcode-select --install`. Linux: `sudo apt install build-essential`. |
| `python3: command not found` | No Python 3 in PATH | Install via https://www.python.org/downloads/ or `brew install python@3.11` |
| `LIVE=1 but GOOGLE_PLACES_API_KEY is not set` | `.env` not loaded | Confirm `.env` is in the repo root and the key value has **no** quotes around it. |
| `403` from Places API | Key restricted or API not enabled | In Cloud Console: Credentials → click the key → Application restrictions = "None" (or add your IPs). Enable "Places API (New)" not the legacy "Places API". |
| Empty `reviews` array | Place has no public reviews | Try a different `place_id`. |
| Groq summary blank | Free-tier rate limit hit | The script falls back to the offline template; reduce subject count or wait 60 s. |

---

## Where to look next

- `n8n/` — the same pipeline as an importable n8n workflow with a node-by-node walkthrough
- `src/main.py` — orchestrator; call `process()` to integrate the pipeline into your own code
- `src/summarize.py` — the LLM vs offline-template branch

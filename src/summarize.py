"""LLM-powered review summarization with a deterministic offline fallback.

`summarize(...)` calls Groq when `GROQ_API_KEY` is set, otherwise produces a
template-based summary so demos and tests run without any API key.
"""

from __future__ import annotations

import os
from typing import Any


def _offline_summary(name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Deterministic template summary — no LLM needed."""
    rating = data.get("rating", 0)
    count = data.get("userRatingCount", 0)
    reviews = data.get("reviews", []) or []
    negative = [r for r in reviews if (r.get("rating") or 5) < 4]
    summary = (
        f"{name} holds a {rating}-star average across {count} reviews; "
        f"{len(negative)} of the {len(reviews)} most-recent reviews are below 4 stars."
    )
    responses = []
    for r in negative[:3]:
        text = ((r.get("text") or {}).get("text") or "")[:300]
        responses.append({
            "reviewer": (r.get("authorAttribution") or {}).get("displayName", "Anonymous"),
            "rating": r.get("rating"),
            "original": text,
            "suggested_reply": (
                "Thank you for sharing your experience. We're sorry to hear it fell short — "
                "we'd like to make this right. Please reach out so we can look into it directly."
            ),
        })
    return {"summary": summary, "responses": responses, "engine": "offline-template"}


def _groq_summary(name: str, data: dict[str, Any], tone: str) -> dict[str, Any]:
    """Live Groq call. Only invoked when GROQ_API_KEY is present."""
    from groq import Groq  # local import keeps the offline demo dependency-light

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    rating = data.get("rating", "N/A")
    count = data.get("userRatingCount", 0)
    reviews = (data.get("reviews") or [])[:5]

    blurbs = "\n".join(
        f"- [{r.get('rating', '?')}★] {((r.get('text') or {}).get('text') or '')[:200]}"
        for r in reviews
    )
    summary_resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": (
                f"Subject: {name}\n"
                f"Average rating: {rating} ({count} total reviews)\n"
                f"Recent reviews:\n{blurbs}\n\n"
                "Write ONE sentence executive summary of this entity's reputation. "
                "Be specific and quantitative where possible. Nothing else."
            ),
        }],
        temperature=0.3,
        max_tokens=120,
    )
    summary = summary_resp.choices[0].message.content.strip()

    responses = []
    for r in reviews:
        rating_val = r.get("rating", 5)
        if rating_val >= 4:
            continue
        text = ((r.get("text") or {}).get("text") or "")[:400]
        if not text:
            continue
        reply_resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"Draft a {tone} response to this {rating_val}-star review (max 80 words):\n\n{text}",
            }],
            temperature=0.4,
            max_tokens=200,
        )
        responses.append({
            "reviewer": (r.get("authorAttribution") or {}).get("displayName", "Anonymous"),
            "rating": rating_val,
            "original": text,
            "suggested_reply": reply_resp.choices[0].message.content.strip(),
        })

    return {"summary": summary, "responses": responses, "engine": "groq:llama-3.3-70b"}


def summarize(name: str, data: dict[str, Any], tone: str = "professional and friendly") -> dict[str, Any]:
    """Return a summary + suggested replies. Uses Groq if available, else offline template."""
    if os.environ.get("GROQ_API_KEY"):
        return _groq_summary(name, data, tone)
    return _offline_summary(name, data)

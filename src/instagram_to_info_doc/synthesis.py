from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from textwrap import shorten

from openai import OpenAI

from .models import VideoCandidate


STOP_WORDS = {
    "the", "and", "that", "this", "with", "from", "have", "your", "about", "what", "they", "them", "their",
    "just", "into", "when", "where", "which", "would", "there", "then", "because", "were", "been", "also",
}


def _extract_keywords(texts: list[str], n: int = 40) -> list[tuple[str, int]]:
    words: list[str] = []
    for t in texts:
        for token in t.lower().split():
            token = "".join(ch for ch in token if ch.isalpha())
            if len(token) < 4 or token in STOP_WORDS:
                continue
            words.append(token)
    return Counter(words).most_common(n)


def _draft_markdown(profile: str, videos: list[VideoCandidate]) -> str:
    transcripts = [v.transcript_text for v in videos if v.transcript_text]
    keywords = _extract_keywords(transcripts)

    lines: list[str] = []
    lines.append(f"# Creator Intelligence Report: @{profile}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(
        f"Analyzed **{len(videos)}** high-performing videos with transcripts. "
        "Selection was based on a weighted score combining view volume and smoothed engagement rate."
    )
    lines.append("")
    lines.append("## Repeated Themes & Vocabulary")
    for kw, count in keywords[:20]:
        lines.append(f"- **{kw}** ({count} mentions)")
    lines.append("")
    lines.append("## Per-video Insight Table")
    lines.append("| Video | Views | Engagement | Core message |"); lines.append("|---|---:|---:|---|")
    for v in videos:
        core = shorten(v.transcript_text.replace("\n", " "), width=160, placeholder="…")
        lines.append(f"| [{v.shortcode}]({v.post_url}) | {v.views:,} | {v.engagement_rate:.2%} | {core} |")

    lines.append("")
    lines.append("## Strategic Interpretation")
    lines.append(
        "Use an LLM pass (`--use-llm-report`) for deeper synthesis, quote-backed value mapping, hook formulas, "
        "positioning, and implementation recommendations."
    )
    return "\n".join(lines)


def generate_report(
    profile: str,
    videos: list[VideoCandidate],
    output_markdown: Path,
    use_llm_report: bool,
    llm_model: str,
) -> Path:
    base_md = _draft_markdown(profile, videos)

    if use_llm_report:
        client = OpenAI()
        payload = [
            {
                "shortcode": v.shortcode,
                "url": v.post_url,
                "views": v.views,
                "engagement_rate": v.engagement_rate,
                "transcript": v.transcript_text,
            }
            for v in videos
        ]
        prompt = (
            "Write a 10-20 page-equivalent strategic consultant report in markdown."
            "Focus on creator values, messaging architecture, hook patterns, audience psychology, "
            "content pillars, and practical playbook. Avoid repetition, but preserve nuance."
            "Use direct quotes from transcripts as evidence.\n\n"
            + json.dumps(payload)[:180000]
        )
        resp = client.responses.create(
            model=llm_model,
            input=[
                {"role": "system", "content": "You are a world-class content strategy analyst."},
                {"role": "user", "content": prompt},
            ],
        )
        llm_md = resp.output_text
        final_md = llm_md if llm_md else base_md
    else:
        final_md = base_md

    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.write_text(final_md, encoding="utf-8")
    return output_markdown

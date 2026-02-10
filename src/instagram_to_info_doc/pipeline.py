from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .config import PipelineConfig
from .instagram import download_video, fetch_video_candidates
from .models import PipelineResult
from .scoring import keep_top_ratio, score_videos
from .synthesis import generate_report
from .transcripts import build_whisper, transcribe_video


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    out_root = config.output_dir / config.profile
    videos_dir = out_root / "videos"
    transcripts_dir = out_root / "transcripts"
    out_root.mkdir(parents=True, exist_ok=True)

    candidates = fetch_video_candidates(config.profile, config.max_posts, config.months_back)
    ranked = score_videos(candidates, min_views_floor=config.min_views_floor)
    shortlisted = keep_top_ratio(ranked, config.keep_ratio)

    whisper = build_whisper(config.whisper_model, config.whisper_device, config.whisper_compute_type)

    kept = []
    for c in shortlisted:
        try:
            video_path = download_video(c, videos_dir)
            txt_path = transcripts_dir / f"{c.shortcode}.txt"
            transcript, detected_language = transcribe_video(
                whisper=whisper,
                video_path=video_path,
                expected_language=config.language,
                transcript_out=txt_path,
            )
            c.transcript_language = detected_language
            if len(transcript) < config.min_transcript_chars:
                c.skip_reason = "missing_or_too_short_transcript"
                continue

            c.transcript_path = txt_path
            c.transcript_text = transcript
            kept.append(c)
        except Exception as exc:  # noqa: BLE001
            c.skip_reason = f"error:{exc}"

    report_path = out_root / "report.md"
    generate_report(
        profile=config.profile,
        videos=kept,
        output_markdown=report_path,
        use_llm_report=config.use_llm_report,
        llm_model=config.llm_model,
    )

    metadata_path = out_root / "metadata.json"
    transcript_manifest = out_root / "transcripts_manifest.json"

    metadata = [asdict(v) for v in ranked]
    for item in metadata:
        for key in ("local_video_path", "transcript_path"):
            if item.get(key):
                item[key] = str(item[key])

    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    manifest = [
        {
            "shortcode": v.shortcode,
            "path": str(v.transcript_path),
            "language": v.transcript_language,
            "chars": len(v.transcript_text),
        }
        for v in kept
    ]
    with transcript_manifest.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return PipelineResult(
        profile=config.profile,
        scanned_count=len(candidates),
        downloaded_count=len(shortlisted),
        with_transcript_count=len(kept),
        final_count=len(kept),
        output_dir=out_root,
        markdown_report=report_path,
        metadata_json=metadata_path,
        transcript_manifest=transcript_manifest,
        notes=[],
    )

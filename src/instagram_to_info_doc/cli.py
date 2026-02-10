from __future__ import annotations

import argparse
from pathlib import Path

from .config import PipelineConfig
from .pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="instagram-to-info-doc",
        description="Build an intelligence report from an Instagram creator's top-performing videos.",
    )
    parser.add_argument("profile", help="Instagram handle without @")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--max-posts", type=int, default=60)
    parser.add_argument("--months-back", type=int, default=18)
    parser.add_argument("--keep-ratio", type=float, default=0.8)
    parser.add_argument("--min-views-floor", type=int, default=500)
    parser.add_argument("--min-transcript-chars", type=int, default=120)
    parser.add_argument("--whisper-model", default="medium")
    parser.add_argument("--whisper-device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument("--whisper-compute-type", default="auto")
    parser.add_argument("--language", default="en")
    parser.add_argument("--use-llm-report", action="store_true")
    parser.add_argument("--llm-model", default="gpt-4o-mini")

    # Auth options for local/private use (to reduce 429s)
    parser.add_argument("--ig-username", default=None)
    parser.add_argument("--ig-password", default=None)
    parser.add_argument("--ig-session-file", default=None)
    parser.add_argument("--ig-cookies-file", default=None)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = PipelineConfig(
        profile=args.profile,
        output_dir=Path(args.output_dir),
        max_posts=args.max_posts,
        months_back=args.months_back,
        keep_ratio=args.keep_ratio,
        min_views_floor=args.min_views_floor,
        min_transcript_chars=args.min_transcript_chars,
        whisper_model=args.whisper_model,
        whisper_device=args.whisper_device,
        whisper_compute_type=args.whisper_compute_type,
        language=args.language,
        use_llm_report=args.use_llm_report,
        llm_model=args.llm_model,
        ig_username=args.ig_username,
        ig_password=args.ig_password,
        ig_session_file=Path(args.ig_session_file) if args.ig_session_file else None,
        ig_cookies_file=Path(args.ig_cookies_file) if args.ig_cookies_file else None,
    )
    result = run_pipeline(config)
    print("Done")
    print(f"Scanned: {result.scanned_count}")
    print(f"Shortlisted(download attempts): {result.downloaded_count}")
    print(f"With transcript: {result.with_transcript_count}")
    print(f"Report: {result.markdown_report}")


if __name__ == "__main__":
    main()

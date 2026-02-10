from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class VideoCandidate:
    shortcode: str
    post_url: str
    caption: str
    is_video: bool
    views: int
    likes: int
    comments: int
    timestamp_iso: str
    owner_username: str
    video_url: Optional[str] = None
    local_video_path: Optional[Path] = None
    transcript_path: Optional[Path] = None
    transcript_text: str = ""
    transcript_language: Optional[str] = None
    engagement_rate: float = 0.0
    weighted_score: float = 0.0
    skip_reason: Optional[str] = None


@dataclass(slots=True)
class PipelineResult:
    profile: str
    scanned_count: int
    downloaded_count: int
    with_transcript_count: int
    final_count: int
    output_dir: Path
    markdown_report: Path
    metadata_json: Path
    transcript_manifest: Path
    notes: list[str] = field(default_factory=list)

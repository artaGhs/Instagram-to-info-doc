from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class PipelineConfig:
    profile: str
    output_dir: Path = Path("output")
    max_posts: int = 60
    months_back: int = 18
    keep_ratio: float = 0.8
    min_views_floor: int = 500
    min_transcript_chars: int = 120
    whisper_model: str = "medium"
    whisper_device: str = "auto"
    whisper_compute_type: str = "auto"
    language: str = "en"
    use_llm_report: bool = False
    llm_model: str = "gpt-4o-mini"

    # Instagram auth options (local/private usage)
    ig_username: Optional[str] = None
    ig_password: Optional[str] = None
    ig_session_file: Optional[Path] = None
    ig_cookies_file: Optional[Path] = None


DEFAULT_SCORE_WEIGHTS: dict[str, float] = {
    "views": 0.55,
    "engagement": 0.35,
    "comments": 0.10,
}

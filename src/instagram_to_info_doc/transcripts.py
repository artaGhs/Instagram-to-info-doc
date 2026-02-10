from __future__ import annotations

from pathlib import Path

from faster_whisper import WhisperModel


def build_whisper(model_name: str, device: str, compute_type: str) -> WhisperModel:
    if device == "auto":
        device = "cuda"
    if compute_type == "auto":
        compute_type = "float16" if device == "cuda" else "int8"
    return WhisperModel(model_name, device=device, compute_type=compute_type)


def transcribe_video(
    whisper: WhisperModel,
    video_path: Path,
    expected_language: str,
    transcript_out: Path,
) -> tuple[str, str]:
    segments, info = whisper.transcribe(str(video_path), beam_size=5, vad_filter=True)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    transcript_out.parent.mkdir(parents=True, exist_ok=True)
    transcript_out.write_text(text, encoding="utf-8")

    detected = info.language or "unknown"
    if expected_language and detected != expected_language:
        return "", detected
    return text, detected

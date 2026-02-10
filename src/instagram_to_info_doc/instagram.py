from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import instaloader

from .models import VideoCandidate


def _build_loader() -> instaloader.Instaloader:
    return instaloader.Instaloader(
        download_comments=False,
        download_geotags=False,
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )


def login_with_session(loader: instaloader.Instaloader, username: str, session_file: str | None) -> None:
    if session_file:
        loader.load_session_from_file(username, filename=session_file)


def fetch_video_candidates(
    profile_name: str,
    max_posts: int,
    months_back: int,
) -> list[VideoCandidate]:
    loader = _build_loader()
    profile = instaloader.Profile.from_username(loader.context, profile_name)

    cutoff = datetime.now(timezone.utc) - timedelta(days=months_back * 30)
    output: list[VideoCandidate] = []

    for post in profile.get_posts():
        if len(output) >= max_posts:
            break
        if post.date_utc.replace(tzinfo=timezone.utc) < cutoff:
            continue
        if not post.is_video:
            continue

        output.append(
            VideoCandidate(
                shortcode=post.shortcode,
                post_url=f"https://www.instagram.com/p/{post.shortcode}/",
                caption=post.caption or "",
                is_video=post.is_video,
                views=post.video_view_count or 0,
                likes=post.likes or 0,
                comments=post.comments or 0,
                timestamp_iso=post.date_utc.isoformat(),
                owner_username=post.owner_username,
                video_url=post.video_url,
            )
        )

    return output


def download_video(candidate: VideoCandidate, out_dir: Path) -> Path:
    if not candidate.video_url:
        raise ValueError(f"Missing video_url for {candidate.shortcode}")

    import yt_dlp

    out_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(out_dir / f"{candidate.shortcode}.%(ext)s")
    opts = {
        "quiet": True,
        "format": "mp4/best",
        "outtmpl": output_template,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([candidate.video_url])

    downloaded = next(out_dir.glob(f"{candidate.shortcode}.*"), None)
    if not downloaded:
        raise FileNotFoundError(f"Failed to find downloaded file for {candidate.shortcode}")
    candidate.local_video_path = downloaded
    return downloaded

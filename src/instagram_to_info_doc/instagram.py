from __future__ import annotations

import os
import random
import time
from datetime import datetime, timedelta, timezone
from http.cookiejar import MozillaCookieJar
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
        max_connection_attempts=3,
        request_timeout=30,
    )


def _apply_cookies_file(loader: instaloader.Instaloader, cookies_file: Path) -> None:
    jar = MozillaCookieJar(str(cookies_file))
    jar.load(ignore_discard=True, ignore_expires=True)
    for cookie in jar:
        if "instagram.com" in cookie.domain:
            loader.context._session.cookies.set_cookie(cookie)  # noqa: SLF001


def authenticate_loader(
    loader: instaloader.Instaloader,
    username: str | None,
    password: str | None,
    session_file: Path | None,
    cookies_file: Path | None,
) -> None:
    env_username = os.getenv("IG_USERNAME")
    env_password = os.getenv("IG_PASSWORD")
    env_session = os.getenv("IG_SESSION_FILE")
    env_cookies = os.getenv("IG_COOKIES_FILE")

    username = username or env_username
    password = password or env_password
    session_file = session_file or (Path(env_session) if env_session else None)
    cookies_file = cookies_file or (Path(env_cookies) if env_cookies else None)

    if cookies_file and cookies_file.exists():
        _apply_cookies_file(loader, cookies_file)

    if username and session_file and session_file.exists():
        loader.load_session_from_file(username, filename=str(session_file))
        return

    if username and password:
        loader.login(username, password)
        if session_file:
            session_file.parent.mkdir(parents=True, exist_ok=True)
            loader.save_session_to_file(filename=str(session_file))


def fetch_video_candidates(
    profile_name: str,
    max_posts: int,
    months_back: int,
    username: str | None = None,
    password: str | None = None,
    session_file: Path | None = None,
    cookies_file: Path | None = None,
) -> list[VideoCandidate]:
    loader = _build_loader()
    authenticate_loader(loader, username, password, session_file, cookies_file)

    cutoff = datetime.now(timezone.utc) - timedelta(days=months_back * 30)
    output: list[VideoCandidate] = []

    try:
        profile = instaloader.Profile.from_username(loader.context, profile_name)
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
    except instaloader.exceptions.TooManyRequestsException as exc:
        # Give a useful message with actionable local auth steps.
        msg = (
            "Instagram rate-limited requests (429). Provide --ig-cookies-file and/or "
            "--ig-session-file with --ig-username (or IG_* env vars) to run authenticated."
        )
        raise RuntimeError(msg) from exc
    except instaloader.exceptions.ConnectionException:
        # minor jittered cool-down before bubbling error.
        time.sleep(random.uniform(1.5, 4.0))
        raise

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

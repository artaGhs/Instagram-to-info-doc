# Instagram to Info Doc

A local-first pipeline that turns an Instagram account's best videos into a detailed strategic analysis report.

## What it does

1. Fetches up to 60 videos from a target profile (default: last 18 months).
2. Scores each video with a weighted formula balancing **view volume** and **engagement quality**.
3. Keeps top 80% by score.
4. Downloads shortlisted videos locally.
5. Runs local transcription with `faster-whisper` (English by default).
6. Skips videos with missing/too-short transcript.
7. Produces:
   - `report.md`
   - `metadata.json`
   - `transcripts_manifest.json`
   - transcript `.txt` files per kept video

## Ranking logic

Weighted score =
- 55% views (z-score)
- 35% Bayesian-smoothed engagement rate `(likes + comments) / views`
- 10% comments (z-score)
- additional penalty when views are below a floor (`--min-views-floor`, default 500)

The Bayesian smoothing prevents tiny-view outliers from dominating the ranking.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Run (quick start)

```bash
instagram-to-info-doc <instagram_handle>
```

## Avoid Instagram 429 / TooManyRequests (recommended)

For local/private usage, run authenticated with your own account session or cookies.

### Option A: Session file + username (recommended)

1. Generate/store a session file once (either by logging in via this tool or via instaloader).
2. Reuse it on future runs.

Run:

```bash
instagram-to-info-doc <instagram_handle> \
  --ig-username your_username \
  --ig-session-file .secrets/ig.session
```

If session file does not exist yet, you can also provide password once:

```bash
instagram-to-info-doc <instagram_handle> \
  --ig-username your_username \
  --ig-password 'your_password' \
  --ig-session-file .secrets/ig.session
```

The tool logs in and saves the session to `.secrets/ig.session` for next time.

### Option B: Browser cookies file (Netscape format)

```bash
instagram-to-info-doc <instagram_handle> \
  --ig-cookies-file /path/to/instagram_cookies.txt
```

### Environment variables alternative

```bash
export IG_USERNAME=your_username
export IG_PASSWORD=your_password
export IG_SESSION_FILE=.secrets/ig.session
export IG_COOKIES_FILE=/path/to/instagram_cookies.txt
instagram-to-info-doc <instagram_handle>
```

## Common full run

```bash
instagram-to-info-doc <instagram_handle> \
  --max-posts 60 \
  --months-back 18 \
  --keep-ratio 0.8 \
  --whisper-model medium \
  --whisper-device auto \
  --language en \
  --ig-username your_username \
  --ig-session-file .secrets/ig.session
```

### Optional LLM final report generation

If you want a deeper 10-20 page consultant-style report, you can enable an API-backed pass:

```bash
export OPENAI_API_KEY=your_key_here
instagram-to-info-doc <instagram_handle> --use-llm-report --llm-model gpt-4o-mini
```

The pipeline remains local for scraping/download/transcription; only the final synthesis call uses the API.

## Output layout

```text
output/<profile>/
  report.md
  metadata.json
  transcripts_manifest.json
  videos/
  transcripts/
```

## Notes

- If Instagram returns `429 TooManyRequests`, use `--ig-session-file` and/or `--ig-cookies-file`.
- For best quality on RTX 3080-class hardware, `--whisper-model medium` or `large-v3` can work.
- This project is intended for local/private usage.

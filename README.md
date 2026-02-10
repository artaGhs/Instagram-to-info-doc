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

## Run

```bash
instagram-to-info-doc <instagram_handle> \
  --max-posts 60 \
  --months-back 18 \
  --keep-ratio 0.8 \
  --whisper-model medium \
  --whisper-device auto \
  --language en
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

- Instagram extraction can break if unauthenticated. Consider using your browser session/cookies workflow (future enhancement).
- For best quality on RTX 3080-class hardware, `--whisper-model medium` or `large-v3` can work.
- This project is intended for local/private usage.

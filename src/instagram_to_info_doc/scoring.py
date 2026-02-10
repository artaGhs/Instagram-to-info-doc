from __future__ import annotations

from statistics import mean, pstdev

from .config import DEFAULT_SCORE_WEIGHTS
from .models import VideoCandidate


def _z_score(values: list[int], x: int) -> float:
    if not values:
        return 0.0
    mu = mean(values)
    sigma = pstdev(values)
    if sigma == 0:
        return 0.0
    return (x - mu) / sigma


def _bayesian_engagement(likes: int, comments: int, views: int, prior: float = 0.03, m: int = 1200) -> float:
    """
    Bayesian smoothed engagement rate to avoid tiny-view outliers dominating ranking.
    """
    raw = (likes + comments) / max(views, 1)
    return (views * raw + m * prior) / (views + m)


def score_videos(candidates: list[VideoCandidate], min_views_floor: int) -> list[VideoCandidate]:
    view_values = [c.views for c in candidates]
    comment_values = [c.comments for c in candidates]

    for c in candidates:
        c.engagement_rate = _bayesian_engagement(c.likes, c.comments, c.views)
        v_component = _z_score(view_values, c.views)
        c_component = _z_score(comment_values, c.comments)
        e_component = c.engagement_rate

        floor_penalty = -1.0 if c.views < min_views_floor else 0.0

        c.weighted_score = (
            DEFAULT_SCORE_WEIGHTS["views"] * v_component
            + DEFAULT_SCORE_WEIGHTS["engagement"] * e_component
            + DEFAULT_SCORE_WEIGHTS["comments"] * c_component
            + floor_penalty
        )

    return sorted(candidates, key=lambda c: c.weighted_score, reverse=True)


def keep_top_ratio(candidates: list[VideoCandidate], keep_ratio: float) -> list[VideoCandidate]:
    if not candidates:
        return []
    keep_count = max(1, int(len(candidates) * keep_ratio))
    return candidates[:keep_count]

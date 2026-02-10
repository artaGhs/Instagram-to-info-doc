from instagram_to_info_doc.models import VideoCandidate
from instagram_to_info_doc.scoring import keep_top_ratio, score_videos


def _c(shortcode: str, views: int, likes: int, comments: int) -> VideoCandidate:
    return VideoCandidate(
        shortcode=shortcode,
        post_url=f"https://www.instagram.com/p/{shortcode}/",
        caption="",
        is_video=True,
        views=views,
        likes=likes,
        comments=comments,
        timestamp_iso="2025-01-01T00:00:00",
        owner_username="creator",
    )


def test_score_penalizes_tiny_view_outlier():
    candidates = [
        _c("A", views=100000, likes=7000, comments=300),
        _c("B", views=120, likes=110, comments=30),
        _c("C", views=45000, likes=2000, comments=140),
    ]
    ranked = score_videos(candidates, min_views_floor=500)
    assert ranked[0].shortcode in {"A", "C"}
    assert ranked[-1].shortcode == "B"


def test_keep_top_ratio_rounds_down_min_one():
    candidates = [_c(str(i), views=1000 + i, likes=40, comments=2) for i in range(5)]
    ranked = score_videos(candidates, min_views_floor=500)
    top = keep_top_ratio(ranked, 0.4)
    assert len(top) == 2

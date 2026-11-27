"""Temporal train/test split for the ML-01 offline benchmark (see eval/SPEC.md)."""

LIKE_THRESHOLD = 3.5
DISLIKE_THRESHOLD = 2.5


def is_liked(rating):
    """Unrated watches are implicit positives."""
    return rating is None or rating >= LIKE_THRESHOLD


def is_disliked(rating):
    return rating is not None and rating <= DISLIKE_THRESHOLD


def temporal_split(events, cutoff):
    """Split events at ``cutoff`` into training events and per-viewer relevant test titles."""
    train = [event for event in events if event["ts"] <= cutoff]
    test = {}
    for event in events:
        if event["ts"] >= cutoff and is_liked(event["rating"]):
            test.setdefault(event["viewer"], set()).add(event["title"])
    return train, {viewer: sorted(titles) for viewer, titles in sorted(test.items())}

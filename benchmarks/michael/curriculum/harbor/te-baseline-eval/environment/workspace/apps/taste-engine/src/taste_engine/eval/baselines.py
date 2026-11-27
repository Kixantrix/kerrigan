"""Baseline A (popularity/genre) and Baseline B (liked-minus-disliked similarity)."""

import math

from .split import is_liked


def candidates(viewer, train, titles):
    seen = {event["title"] for event in train if event["viewer"] == viewer}
    return [title for title in titles if title["id"] not in seen]


def popularity_genre_rank(viewer, train, titles, k=20):
    """Rank unseen titles by liked-genre overlap, then household popularity."""
    watchers = {}
    for event in train:
        watchers.setdefault(event["title"], set()).add(event["viewer"])
    genres = {title["id"]: title["genres"] for title in titles}
    liked_genres = set()
    for event in train:
        if event["viewer"] == viewer and is_liked(event["rating"]):
            liked_genres.update(genres.get(event["title"], ()))
    ranked = sorted(candidates(viewer, train, titles), key=lambda title: (
        -len(liked_genres.intersection(title["genres"])),
        -len(watchers.get(title["id"], ())), title["id"]))
    return [title["id"] for title in ranked[:k]]


def cosine(left, right):
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def similarity_rank(viewer, train, titles, k=20):
    """Rank unseen titles by cosine similarity to the viewer's watched titles."""
    embeddings = {title["id"]: title["embedding"] for title in titles}
    width = len(titles[0]["embedding"]) if titles else 0
    watched = [embeddings[event["title"]] for event in train
               if event["viewer"] == viewer and event["title"] in embeddings]
    profile = [sum(vector[i] for vector in watched) / len(watched) if watched else 0.0
               for i in range(width)]
    ranked = sorted(candidates(viewer, train, titles), key=lambda title: (
        -cosine(profile, title["embedding"]), title["id"]))
    return [title["id"] for title in ranked[:k]]

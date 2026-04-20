"""Trick resolution for German Whist."""

from __future__ import annotations

from whist.core.card import Card, Suit


def resolve_trick(lead: Card, follow: Card, trump: Suit) -> int:
    """Determine the winner of a trick.

    Args:
        lead: Card played by the leader.
        follow: Card played by the follower.
        trump: The trump suit for this game.

    Returns:
        0 if the leader wins, 1 if the follower wins.
    """
    if follow.suit == lead.suit:
        # Same suit: higher rank wins
        return 0 if lead.rank > follow.rank else 1
    elif follow.suit == trump:
        # Follower trumped
        return 1
    else:
        # Follower played off-suit (not trump): leader wins
        return 0

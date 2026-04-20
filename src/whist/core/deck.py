"""Deck creation, shuffling, and dealing for German Whist."""

from __future__ import annotations

import random
from dataclasses import dataclass

from whist.core.card import ALL_CARDS, Card, Suit


@dataclass
class Deal:
    """Result of dealing for a German Whist game."""
    hand0: list[Card]  # Non-dealer's hand
    hand1: list[Card]  # Dealer's hand
    stock: list[Card]  # Remaining 26 cards, index 0 = top (face-up)
    trump: Suit        # Trump suit (suit of top stock card)


def deal(rng: random.Random | None = None) -> Deal:
    """Shuffle and deal a German Whist game.

    Returns hands for both players (13 each) and a 26-card stock
    with the top card face-up determining the trump suit.
    """
    if rng is None:
        rng = random.Random()

    cards = list(ALL_CARDS)
    rng.shuffle(cards)

    hand0 = cards[0:13]
    hand1 = cards[13:26]
    stock = cards[26:]  # 26 cards, index 0 is top (face-up)

    trump = stock[0].suit

    return Deal(hand0=hand0, hand1=hand1, stock=stock, trump=trump)

"""Hand evaluation heuristics for German Whist AI.

Used by ISMCTS for rollout evaluation and position assessment.
"""

from __future__ import annotations

from whist.core.card import Card, Rank, Suit


def evaluate_hand(hand: frozenset[Card], trump: Suit) -> float:
    """Evaluate hand strength for Phase 2 potential.

    Returns a score where higher = better hand.
    """
    score = 0.0

    # Group by suit
    suits: dict[Suit, list[Card]] = {}
    for card in hand:
        suits.setdefault(card.suit, []).append(card)

    for suit, cards in suits.items():
        cards_sorted = sorted(cards, key=lambda c: c.rank, reverse=True)
        is_trump = (suit == trump)
        multiplier = 1.5 if is_trump else 1.0

        # High card points
        for card in cards_sorted:
            if card.rank == Rank.ACE:
                score += 4.0 * multiplier
            elif card.rank == Rank.KING:
                score += 3.0 * multiplier
            elif card.rank == Rank.QUEEN:
                score += 2.0 * multiplier
            elif card.rank == Rank.JACK:
                score += 1.0 * multiplier

        # Suit length (more cards = more control)
        length = len(cards)
        if is_trump:
            # Trump length is very valuable
            if length >= 4:
                score += (length - 3) * 3.0
            elif length >= 2:
                score += (length - 1) * 1.0
        else:
            # Long side suits can establish winners
            if length >= 4:
                score += (length - 3) * 1.5

    # Void suits (excluding trump) = trumping potential
    for suit in Suit:
        if suit != trump and suit not in suits:
            trump_cards = suits.get(trump, [])
            if trump_cards:
                score += 2.0

    return score


def evaluate_face_up_value(
    face_up: Card,
    hand: frozenset[Card],
    trump: Suit,
) -> float:
    """Evaluate how desirable the face-up card is to win.

    Higher = more desirable.
    """
    score = 0.0

    # Base value from rank
    if face_up.rank == Rank.ACE:
        score += 10.0
    elif face_up.rank == Rank.KING:
        score += 7.0
    elif face_up.rank == Rank.QUEEN:
        score += 5.0
    elif face_up.rank == Rank.JACK:
        score += 3.0
    elif face_up.rank == Rank.TEN:
        score += 2.0
    else:
        score += 0.5

    # Trump bonus
    if face_up.suit == trump:
        score *= 1.5

    # Synergy with hand
    same_suit = [c for c in hand if c.suit == face_up.suit]
    if same_suit:
        # Extends an existing suit
        score += len(same_suit) * 0.5
        # High cards in same suit: the face-up helps establish
        if any(c.rank >= Rank.QUEEN for c in same_suit):
            score += 1.0
    elif face_up.suit != trump:
        # Adding a singleton in a new suit is less useful
        score -= 2.0

    return score

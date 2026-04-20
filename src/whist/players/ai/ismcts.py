"""Phase 1 strategy for AI: determinized win/lose decision.

The key insight: Phase 1 decisions decompose into:
1. Should I try to win or lose this trick? (based on face-up card desirability)
2. What's the best card to play to achieve that goal? (cheapest winner or lowest shed)

We use determinized sampling to make decision #1, then use clean tactical
logic for decision #2.
"""

from __future__ import annotations

import random
from typing import Optional

from whist.core.card import Card, Rank, Suit, FULL_DECK
from whist.core.trick import resolve_trick
from whist.players.ai.evaluator import evaluate_face_up_value


def determinized_choose(
    my_hand: frozenset[Card],
    trump: Suit,
    leader: int,
    my_player: int,
    lead_card: Optional[Card],
    face_up: Optional[Card],
    known_cards: set[Card],
    opponent_known: set[Card],
    stock_remaining: int,
    num_samples: int = 30,
    rng: random.Random | None = None,
) -> Card:
    """Choose a Phase 1 card using determinized win/lose evaluation.

    Step 1: Decide whether to try to win or lose (based on face-up card value).
    Step 2: Pick the optimal card to execute that decision.
    """
    if rng is None:
        rng = random.Random()

    # Determine legal moves
    if lead_card is None:
        legal = sorted(my_hand)
    else:
        led_suit = lead_card.suit
        in_suit = [c for c in my_hand if c.suit == led_suit]
        legal = sorted(in_suit) if in_suit else sorted(my_hand)

    if len(legal) == 1:
        return legal[0]

    # Step 1: Should we win or lose?
    want_to_win = _should_win(my_hand, trump, face_up, known_cards,
                               opponent_known, stock_remaining, num_samples, rng)

    # Step 2: Pick the best card to achieve the goal
    if lead_card is None:
        # We're leading
        return _pick_lead(legal, my_hand, trump, want_to_win, opponent_known,
                          known_cards, num_samples, rng)
    else:
        # We're following
        return _pick_follow(legal, lead_card, trump, want_to_win)


def _should_win(
    my_hand: frozenset[Card],
    trump: Suit,
    face_up: Optional[Card],
    known_cards: set[Card],
    opponent_known: set[Card],
    stock_remaining: int,
    num_samples: int,
    rng: random.Random,
) -> bool:
    """Decide whether to try to win the current trick.

    Compares value of the known face-up card vs expected value of the
    unknown face-down card.
    """
    if face_up is None:
        return True

    # Value of the face-up card (adjusted for our hand)
    face_up_value = evaluate_face_up_value(face_up, my_hand, trump)

    # Expected value of face-down card: average over unknown cards
    unknown = list(FULL_DECK - known_cards - opponent_known)
    if not unknown:
        return face_up_value > 3.0

    # Sample face-down cards and compute average value
    n = min(num_samples, len(unknown))
    sample = rng.sample(unknown, n) if n < len(unknown) else unknown
    avg_fd_value = sum(evaluate_face_up_value(c, my_hand, trump) for c in sample) / len(sample)

    # Win if face-up is significantly better than expected face-down
    # Use a threshold to avoid fighting for marginal cards
    return face_up_value > avg_fd_value + 1.0


def _pick_lead(
    legal: list[Card],
    my_hand: frozenset[Card],
    trump: Suit,
    want_to_win: bool,
    opponent_known: set[Card],
    known_cards: set[Card],
    num_samples: int,
    rng: random.Random,
) -> Card:
    """Pick the best card to lead.

    If we want to win: lead from a suit where we're strong (likely to win).
    If we want to lose: lead low cards the opponent will likely beat.
    """
    if want_to_win:
        # Lead a high card that's likely to win
        # Prefer non-trump high cards (save trumps) unless face-up is trump
        non_trump_high = [c for c in legal if c.suit != trump and c.rank >= Rank.JACK]
        if non_trump_high:
            return max(non_trump_high, key=lambda c: c.rank)

        trump_high = [c for c in legal if c.suit == trump and c.rank >= Rank.JACK]
        if trump_high:
            return max(trump_high, key=lambda c: c.rank)

        # Lead highest card overall
        return max(legal, key=lambda c: (c.suit == trump, c.rank))
    else:
        # Lead low to lose: pick lowest non-trump card
        non_trump = [c for c in legal if c.suit != trump]
        if non_trump:
            return min(non_trump, key=lambda c: c.rank)
        # Only have trumps: lead lowest trump
        return min(legal, key=lambda c: c.rank)


def _pick_follow(
    legal: list[Card],
    lead_card: Card,
    trump: Suit,
    want_to_win: bool,
) -> Card:
    """Pick the best card to follow.

    If we want to win: play the cheapest card that beats the lead.
    If we want to lose: play the lowest card (dumping).
    """
    if want_to_win:
        # Try to win as cheaply as possible
        winners = []
        losers = []
        for card in legal:
            if _would_win(card, lead_card, trump):
                winners.append(card)
            else:
                losers.append(card)

        if winners:
            # Play cheapest winner
            return min(winners, key=lambda c: c.rank)
        # Can't win — dump the lowest
        return _lowest_card(legal, trump)
    else:
        # Try to lose: play the lowest card
        return _lowest_card(legal, trump)


def _would_win(card: Card, lead: Card, trump: Suit) -> bool:
    """Would this card win against the lead?"""
    if card.suit == lead.suit:
        return card.rank > lead.rank
    elif card.suit == trump:
        return True
    return False


def _lowest_card(cards: list[Card], trump: Suit) -> Card:
    """Pick the lowest card, preferring non-trumps."""
    non_trump = [c for c in cards if c.suit != trump]
    pool = non_trump if non_trump else cards
    return min(pool, key=lambda c: c.rank)

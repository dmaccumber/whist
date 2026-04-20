"""Alpha-beta minimax solver for Phase 2 (perfect information endgame).

Uses a C++ extension (via pybind11) for exact solving of all positions
up to 13 cards per player.
"""

from __future__ import annotations

from typing import Optional

from whist.core.card import Card, Suit, ALL_CARDS
from whist._minimax_cpp import solve as _cpp_solve


def _hand_to_mask(hand: frozenset[Card]) -> int:
    mask = 0
    for c in hand:
        mask |= (1 << c.id)
    return mask


def solve_phase2(
    hands: tuple[frozenset[Card], frozenset[Card]],
    trump: Suit,
    leader: int,
    lead_card: Optional[Card] = None,
) -> tuple[int, Optional[Card]]:
    """Solve a Phase 2 position exactly.

    Returns (tricks_for_player_0, best_card_to_play).
    """
    mask0 = _hand_to_mask(hands[0])
    mask1 = _hand_to_mask(hands[1])
    lead_id = lead_card.id if lead_card else -1

    score, best_id = _cpp_solve(mask0, mask1, int(trump), leader, lead_id)

    best_card = ALL_CARDS[best_id] if best_id >= 0 else None
    return (score, best_card)


solve_phase2_exact = solve_phase2

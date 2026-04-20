"""Alpha-beta minimax solver for Phase 2 (perfect information endgame).

Uses a C++ extension (via pybind11) for fast exact solving of all
positions up to 13 cards per player. Falls back to a Python
implementation if the C++ module is unavailable.
"""

from __future__ import annotations

from typing import Optional

from whist.core.card import Card, Suit, ALL_CARDS

# Pre-compute suit masks
_SUIT_MASKS = [0, 0, 0, 0]
for _s in range(4):
    for _r in range(13):
        _SUIT_MASKS[_s] |= (1 << (_r * 4 + _s))

# Try to import C++ solver
try:
    from whist._minimax_cpp import solve as _cpp_solve
    _USE_CPP = True
except ImportError:
    _USE_CPP = False


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

    if _USE_CPP:
        score, best_id = _cpp_solve(mask0, mask1, int(trump), leader, lead_id)
    else:
        masks = [mask0, mask1]
        tt: dict = {}
        score, best_id = _ab_exact(masks, int(trump), leader, lead_id, 0, 14, tt)

    best_card = ALL_CARDS[best_id] if best_id >= 0 else None
    return (score, best_card)


# Alias for backward compatibility with tests
solve_phase2_exact = solve_phase2


# --- Python fallback (used when C++ module is unavailable) ---

def _iter_bits_desc(mask: int) -> list[int]:
    result = []
    m = mask
    while m:
        bit = m & (-m)
        result.append(bit.bit_length() - 1)
        m ^= bit
    result.reverse()
    return result


def _iter_bits_asc(mask: int) -> list[int]:
    result = []
    m = mask
    while m:
        bit = m & (-m)
        result.append(bit.bit_length() - 1)
        m ^= bit
    return result


def _ab_exact(
    masks: list[int],
    trump_int: int,
    leader: int,
    lead_id: int,
    alpha: int,
    beta: int,
    tt: dict,
) -> tuple[int, int]:
    """Exact alpha-beta (Python fallback)."""
    if masks[0] == 0 and masks[1] == 0:
        return (0, -1)
    if lead_id < 0 and (masks[0] == 0 or masks[1] == 0):
        return (0, -1)

    key = (masks[0], masks[1], leader, lead_id)
    cached = tt.get(key)
    if cached is not None:
        return cached

    if lead_id < 0:
        current = leader
        legal_mask = masks[current]
        maximizing = (current == 0)
        card_ids = _iter_bits_desc(legal_mask)

        best_score = -1 if maximizing else 14
        best_cid = card_ids[0]

        for cid in card_ids:
            masks[current] ^= (1 << cid)
            score, _ = _ab_exact(masks, trump_int, leader, cid, alpha, beta, tt)
            masks[current] ^= (1 << cid)

            if maximizing:
                if score > best_score:
                    best_score = score
                    best_cid = cid
                alpha = max(alpha, score)
            else:
                if score < best_score:
                    best_score = score
                    best_cid = cid
                beta = min(beta, score)

            if beta <= alpha:
                break
    else:
        follower = 1 - leader
        hand_mask = masks[follower]
        led_suit = lead_id & 3
        in_suit = hand_mask & _SUIT_MASKS[led_suit]
        legal_mask = in_suit if in_suit else hand_mask

        maximizing = (follower == 0)
        card_ids = _iter_bits_asc(legal_mask)

        best_score = -1 if maximizing else 14
        best_cid = card_ids[0]
        lead_rank_idx = lead_id >> 2

        for cid in card_ids:
            follow_suit = cid & 3
            follow_rank_idx = cid >> 2
            if follow_suit == led_suit:
                winner_offset = 0 if lead_rank_idx > follow_rank_idx else 1
            elif follow_suit == trump_int:
                winner_offset = 1
            else:
                winner_offset = 0

            trick_winner = leader ^ winner_offset
            bonus = 1 if trick_winner == 0 else 0

            masks[follower] ^= (1 << cid)
            sub_score, _ = _ab_exact(masks, trump_int, trick_winner, -1, alpha, beta, tt)
            masks[follower] ^= (1 << cid)

            score = sub_score + bonus

            if maximizing:
                if score > best_score:
                    best_score = score
                    best_cid = cid
                alpha = max(alpha, score)
            else:
                if score < best_score:
                    best_score = score
                    best_cid = cid
                beta = min(beta, score)

            if beta <= alpha:
                break

    tt[key] = (best_score, best_cid)
    return (best_score, best_cid)

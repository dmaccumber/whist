"""Alpha-beta minimax solver for Phase 2 (perfect information endgame).

Uses bitmask hand representation. For positions with <=7 cards each,
solves exactly. For larger positions, uses a 4-trick lookahead with
quick-trick counting heuristic.
"""

from __future__ import annotations

from typing import Optional

from whist.core.card import Card, Suit, ALL_CARDS

# Exact solve threshold (cards per player)
# 10 cards solves in <100ms; AI uses heuristic for larger hands
_EXACT_LIMIT = 10

# Pre-compute suit masks
_SUIT_MASKS = [0, 0, 0, 0]
for _s in range(4):
    for _r in range(13):
        _SUIT_MASKS[_s] |= (1 << (_r * 4 + _s))


def _hand_to_mask(hand: frozenset[Card]) -> int:
    mask = 0
    for c in hand:
        mask |= (1 << c.id)
    return mask


def _popcount(x: int) -> int:
    return bin(x).count('1')


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


def _highest_bit(mask: int) -> int:
    """Return ID of the highest set bit, or -1 if empty."""
    if mask == 0:
        return -1
    return mask.bit_length() - 1


def _quick_tricks(masks: list[int], trump_int: int, leader: int) -> float:
    """Estimate tricks for player 0 using quick-trick counting.

    Counts sure winners (top cards in each suit) and probable winners.
    """
    all_cards = masks[0] | masks[1]
    score = 0.0

    for player in (0, 1):
        hand = masks[player]
        sign = 1.0 if player == 0 else -1.0

        for suit in range(4):
            my_suit = hand & _SUIT_MASKS[suit]
            all_suit = all_cards & _SUIT_MASKS[suit]
            opp_suit = all_suit ^ my_suit

            if not my_suit:
                # Void: trumping potential
                if suit != trump_int:
                    my_trumps = hand & _SUIT_MASKS[trump_int]
                    opp_in_suit = (masks[1 - player]) & _SUIT_MASKS[suit]
                    if my_trumps and opp_in_suit:
                        # Can trump opponent's leads in this suit
                        n_ruff = min(_popcount(my_trumps), _popcount(opp_in_suit))
                        score += sign * n_ruff * 0.4
                continue

            # Count top winners: consecutive top cards we hold
            remaining_all = all_suit
            remaining_mine = my_suit
            winners = 0.0
            while remaining_all and remaining_mine:
                top = _highest_bit(remaining_all)
                top_bit = 1 << top
                if remaining_mine & top_bit:
                    winners += 1.0
                    remaining_mine ^= top_bit
                else:
                    break
                remaining_all ^= top_bit

            score += sign * winners

            # Length advantage: if we have more cards in a suit than opponent
            my_count = _popcount(my_suit)
            opp_count = _popcount(opp_suit)
            if my_count > opp_count and opp_count > 0:
                # Long suit: after opponent runs out, remaining cards are winners
                extra = my_count - opp_count
                score += sign * extra * 0.35

    # Lead bonus: having the lead with winners is valuable
    leader_hand = masks[leader]
    for suit in range(4):
        my_suit = leader_hand & _SUIT_MASKS[suit]
        all_suit = all_cards & _SUIT_MASKS[suit]
        if my_suit and all_suit:
            top = _highest_bit(all_suit)
            if my_suit & (1 << top):
                score += (1.0 if leader == 0 else -1.0) * 0.15

    return score


def solve_phase2(
    hands: tuple[frozenset[Card], frozenset[Card]],
    trump: Suit,
    leader: int,
    lead_card: Optional[Card] = None,
) -> tuple[int, Optional[Card]]:
    """Solve a Phase 2 position.

    Returns (estimated_tricks_for_player_0, best_card_to_play).
    """
    masks = [_hand_to_mask(hands[0]), _hand_to_mask(hands[1])]
    lead_id = lead_card.id if lead_card else -1
    n_cards = _popcount(masks[0])

    if n_cards <= _EXACT_LIMIT:
        tt: dict = {}
        score, best_id = _ab_exact(masks, int(trump), leader, lead_id, 0, 14, tt)
    else:
        # Shallow search: 3-trick lookahead, then exact at 10 cards
        max_tricks = 3
        tt = {}
        exact_tt = {}  # Shared across all leaf exact solves
        score_f, best_id = _ab_shallow(masks, int(trump), leader, lead_id, 0, max_tricks * 2, -100.0, 100.0, tt, exact_tt)
        score = round(score_f)

    best_card = ALL_CARDS[best_id] if best_id >= 0 else None
    return (score, best_card)


def solve_phase2_exact(
    hands: tuple[frozenset[Card], frozenset[Card]],
    trump: Suit,
    leader: int,
    lead_card: Optional[Card] = None,
) -> tuple[int, Optional[Card]]:
    """Always solve exactly (for small hands or testing)."""
    masks = [_hand_to_mask(hands[0]), _hand_to_mask(hands[1])]
    lead_id = lead_card.id if lead_card else -1
    tt: dict = {}
    score, best_id = _ab_exact(masks, int(trump), leader, lead_id, 0, 14, tt)
    best_card = ALL_CARDS[best_id] if best_id >= 0 else None
    return (score, best_card)


def _ab_shallow(
    masks: list[int],
    trump_int: int,
    leader: int,
    lead_id: int,
    depth: int,
    max_depth: int,
    alpha: float,
    beta: float,
    tt: dict,
    exact_tt: dict | None = None,
) -> tuple[float, int]:
    """Shallow alpha-beta with heuristic leaf evaluation and pruning."""
    if masks[0] == 0 and masks[1] == 0:
        return (0.0, -1)
    if lead_id < 0 and (masks[0] == 0 or masks[1] == 0):
        return (0.0, -1)

    n_cards = _popcount(masks[0])

    # Switch to exact solve when hands are small
    if n_cards <= _EXACT_LIMIT and lead_id < 0:
        ett = exact_tt if exact_tt is not None else {}
        s, b = _ab_exact(masks, trump_int, leader, lead_id, 0, 14, ett)
        return (float(s), b)

    # At depth limit, evaluate
    if depth >= max_depth and lead_id < 0:
        ev = _quick_tricks(masks, trump_int, leader)
        return (ev, -1)

    if lead_id < 0:
        current = leader
        legal_mask = masks[current]
        maximizing = (current == 0)
        card_ids = _iter_bits_desc(legal_mask)

        best_score = -100.0 if maximizing else 100.0
        best_cid = card_ids[0]

        for cid in card_ids:
            masks[current] ^= (1 << cid)
            score, _ = _ab_shallow(masks, trump_int, leader, cid, depth + 1, max_depth, alpha, beta, tt, exact_tt)
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

        best_score = -100.0 if maximizing else 100.0
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
            bonus = 1.0 if trick_winner == 0 else 0.0

            masks[follower] ^= (1 << cid)
            sub_score, _ = _ab_shallow(masks, trump_int, trick_winner, -1, depth + 1, max_depth, alpha, beta, tt, exact_tt)
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

    return (best_score, best_cid)


def _ab_exact(
    masks: list[int],
    trump_int: int,
    leader: int,
    lead_id: int,
    alpha: int,
    beta: int,
    tt: dict,
) -> tuple[int, int]:
    """Exact alpha-beta for positions with <=7 cards each."""
    if masks[0] == 0 and masks[1] == 0:
        return (0, -1)
    # One hand empty but other isn't — shouldn't happen in a valid game
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

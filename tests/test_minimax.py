"""Tests for minimax solver."""

from whist.core.card import Card, Suit, Rank
from whist.players.ai.minimax import solve_phase2


def test_single_card_leader_wins():
    h0 = frozenset([Card(Rank.ACE, Suit.HEARTS)])
    h1 = frozenset([Card(Rank.KING, Suit.HEARTS)])
    score, best = solve_phase2((h0, h1), Suit.SPADES, leader=0)
    assert score == 1
    assert best == Card(Rank.ACE, Suit.HEARTS)


def test_single_card_follower_wins():
    h0 = frozenset([Card(Rank.TWO, Suit.HEARTS)])
    h1 = frozenset([Card(Rank.ACE, Suit.HEARTS)])
    score, best = solve_phase2((h0, h1), Suit.SPADES, leader=0)
    assert score == 0  # P0 leads 2H, P1 follows AH, P1 wins


def test_trump_beats_off_suit():
    h0 = frozenset([Card(Rank.TWO, Suit.SPADES)])
    h1 = frozenset([Card(Rank.ACE, Suit.HEARTS)])
    # P0 leads 2S (trump), P1 has AH (can't follow spades, plays AH)
    # P0 wins because leader's card stands when follower plays off-suit
    score, best = solve_phase2((h0, h1), Suit.SPADES, leader=0)
    assert score == 1


def test_two_cards_optimal():
    h0 = frozenset([Card(Rank.ACE, Suit.HEARTS), Card(Rank.TWO, Suit.CLUBS)])
    h1 = frozenset([Card(Rank.KING, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS)])
    # P0 leads: if AH -> wins trick 1, then leads 2C, P1 plays AC -> P1 wins trick 2. Score: 1
    # P0 leads: if 2C -> P1 plays AC, P1 wins, leads KH, P0 must follow... but P0 has AH -> P0 wins. Score: 1
    # Either way P0 gets exactly 1 trick
    score, best = solve_phase2((h0, h1), Suit.SPADES, leader=0)
    assert score == 1


def test_three_card_endgame():
    h0 = frozenset([
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.ACE, Suit.CLUBS),
    ])
    h1 = frozenset([
        Card(Rank.QUEEN, Suit.HEARTS),
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.KING, Suit.CLUBS),
    ])
    # P0 dominates: AH beats QH, KH beats 2H, AC beats KC
    score, best = solve_phase2((h0, h1), Suit.SPADES, leader=0)
    assert score == 3


def test_terminal_position():
    h0 = frozenset()
    h1 = frozenset()
    score, best = solve_phase2((h0, h1), Suit.SPADES, leader=0)
    assert score == 0
    assert best is None

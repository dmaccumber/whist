"""Tests for game state and game controller."""

import random

from whist.core.card import Card, Suit, Rank
from whist.core.deck import deal
from whist.core.game import Game
from whist.core.game_state import GameState, Observation, Phase
from whist.players.random_player import RandomPlayer


def test_deal():
    d = deal(random.Random(42))
    assert len(d.hand0) == 13
    assert len(d.hand1) == 13
    assert len(d.stock) == 26
    all_cards = set(d.hand0) | set(d.hand1) | set(d.stock)
    assert len(all_cards) == 52


def test_initial_state():
    d = deal(random.Random(42))
    state = GameState.initial(
        frozenset(d.hand0), frozenset(d.hand1), tuple(d.stock), d.trump,
    )
    assert state.phase == Phase.PHASE1
    assert state.leader == 0
    assert state.lead_card is None
    assert state.current_player == 0
    assert not state.is_terminal
    assert state.face_up == d.stock[0]


def test_legal_moves_leader():
    d = deal(random.Random(42))
    state = GameState.initial(
        frozenset(d.hand0), frozenset(d.hand1), tuple(d.stock), d.trump,
    )
    moves = state.legal_moves()
    assert len(moves) == 13  # Leader can play anything


def test_legal_moves_follower_must_follow():
    d = deal(random.Random(42))
    state = GameState.initial(
        frozenset(d.hand0), frozenset(d.hand1), tuple(d.stock), d.trump,
    )
    # Leader plays first card
    lead = state.legal_moves()[0]
    state2 = state.play_card(lead)
    moves = state2.legal_moves()
    # All moves should be in led suit (if possible)
    follower_hand = state2.hands[state2.current_player]
    in_suit = [c for c in follower_hand if c.suit == lead.suit]
    if in_suit:
        assert all(c.suit == lead.suit for c in moves)


def test_phase1_draws_from_stock():
    d = deal(random.Random(42))
    state = GameState.initial(
        frozenset(d.hand0), frozenset(d.hand1), tuple(d.stock), d.trump,
    )
    lead = state.legal_moves()[0]
    state = state.play_card(lead)
    follow = state.legal_moves()[0]
    state = state.play_card(follow)

    # After one trick in Phase 1:
    assert state.phase == Phase.PHASE1
    assert len(state.stock) == 24  # 26 - 2
    assert len(state.hands[0]) == 13  # Still 13 cards each
    assert len(state.hands[1]) == 13


def test_phase_transition():
    """After 13 Phase 1 tricks, game transitions to Phase 2."""
    d = deal(random.Random(42))
    state = GameState.initial(
        frozenset(d.hand0), frozenset(d.hand1), tuple(d.stock), d.trump,
    )

    rng = random.Random(99)
    for _ in range(13):
        assert state.phase == Phase.PHASE1
        moves = state.legal_moves()
        state = state.play_card(rng.choice(moves))
        moves = state.legal_moves()
        state = state.play_card(rng.choice(moves))

    assert state.phase == Phase.PHASE2
    assert len(state.stock) == 0
    assert len(state.hands[0]) == 13
    assert len(state.hands[1]) == 13


def test_full_game_random():
    """A full game between random players completes correctly."""
    rng = random.Random(42)
    p0 = RandomPlayer(random.Random(1))
    p1 = RandomPlayer(random.Random(2))
    game = Game(players=(p0, p1), rng=rng)
    result = game.play()

    assert result.phase2_tricks[0] + result.phase2_tricks[1] == 13
    assert result.winner in (0, 1, None)
    assert len(result.tricks) == 26


def test_many_random_games():
    """Run 1000 random games — all should complete without errors."""
    for i in range(1000):
        p0 = RandomPlayer(random.Random(i * 2))
        p1 = RandomPlayer(random.Random(i * 2 + 1))
        game = Game(players=(p0, p1), rng=random.Random(i + 10000))
        result = game.play()
        assert result.phase2_tricks[0] + result.phase2_tricks[1] == 13
        assert result.winner in (0, 1)  # 13 tricks => no draws


def test_observation():
    d = deal(random.Random(42))
    state = GameState.initial(
        frozenset(d.hand0), frozenset(d.hand1), tuple(d.stock), d.trump,
    )
    obs = Observation.from_state(state, player=0)
    assert obs.my_hand == state.hands[0]
    assert obs.i_am_player == 0
    assert obs.trump == d.trump
    assert obs.phase == Phase.PHASE1
    assert obs.face_up == d.stock[0]

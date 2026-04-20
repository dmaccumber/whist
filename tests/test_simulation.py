"""Tests for simulation runner."""

import random

from whist.players.random_player import RandomPlayer
from whist.players.heuristic import HeuristicPlayer
from whist.simulation.runner import run_games


def test_run_random_games():
    result = run_games(
        n_games=100,
        player0_factory=lambda: RandomPlayer(random.Random()),
        player1_factory=lambda: RandomPlayer(random.Random()),
        player0_name="Random A",
        player1_name="Random B",
        seed=42,
    )
    assert result.n_games == 100
    assert result.p0_wins + result.p1_wins + result.draws == 100
    # All games should have valid trick counts
    for r in result.results:
        assert r.phase2_tricks[0] + r.phase2_tricks[1] == 13


def test_heuristic_beats_random():
    """Heuristic player should beat random most of the time."""
    result = run_games(
        n_games=200,
        player0_factory=HeuristicPlayer,
        player1_factory=lambda: RandomPlayer(random.Random()),
        player0_name="Heuristic",
        player1_name="Random",
        seed=42,
    )
    # Heuristic should win at least 70% of games
    assert result.p0_win_rate > 0.7, f"Heuristic only won {result.p0_win_rate:.1%}"

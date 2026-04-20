"""Simulation runner — play many games and collect statistics."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from whist.core.game import Game, GameResult
from whist.players.base import BasePlayer


@dataclass
class SimulationResult:
    """Results from a batch of simulated games."""
    player0_type: str
    player1_type: str
    results: list[GameResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    @property
    def n_games(self) -> int:
        return len(self.results)

    @property
    def p0_wins(self) -> int:
        return sum(1 for r in self.results if r.winner == 0)

    @property
    def p1_wins(self) -> int:
        return sum(1 for r in self.results if r.winner == 1)

    @property
    def draws(self) -> int:
        return sum(1 for r in self.results if r.winner is None)

    @property
    def p0_win_rate(self) -> float:
        return self.p0_wins / self.n_games if self.n_games else 0.0

    @property
    def p1_win_rate(self) -> float:
        return self.p1_wins / self.n_games if self.n_games else 0.0

    @property
    def avg_score_diff(self) -> float:
        return sum(r.score_diff for r in self.results) / self.n_games if self.n_games else 0.0

    @property
    def p0_avg_tricks(self) -> float:
        return sum(r.phase2_tricks[0] for r in self.results) / self.n_games if self.n_games else 0.0

    @property
    def p1_avg_tricks(self) -> float:
        return sum(r.phase2_tricks[1] for r in self.results) / self.n_games if self.n_games else 0.0


PlayerFactory = Callable[[], BasePlayer]


def run_games(
    n_games: int,
    player0_factory: Optional[PlayerFactory] = None,
    player1_factory: Optional[PlayerFactory] = None,
    player0_name: str = "Player 0",
    player1_name: str = "Player 1",
    seed: int | None = None,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> SimulationResult:
    """Run N games between two player types.

    If no factories are provided, uses HeuristicPlayer for both.
    """
    if player0_factory is None:
        from whist.players.heuristic import HeuristicPlayer
        player0_factory = HeuristicPlayer
        player0_name = "Heuristic"

    if player1_factory is None:
        from whist.players.heuristic import HeuristicPlayer
        player1_factory = HeuristicPlayer
        player1_name = "Heuristic"

    rng = random.Random(seed)
    result = SimulationResult(
        player0_type=player0_name,
        player1_type=player1_name,
    )

    start = time.time()
    for i in range(n_games):
        p0 = player0_factory()
        p1 = player1_factory()
        game = Game(players=(p0, p1), rng=random.Random(rng.randint(0, 2**31)))
        game_result = game.play()
        result.results.append(game_result)

        if progress_callback and (i + 1) % 100 == 0:
            progress_callback(i + 1, n_games)

    result.elapsed_seconds = time.time() - start
    return result

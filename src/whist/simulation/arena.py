"""Arena — tournament between different player types."""

from __future__ import annotations

import random
from typing import Optional

from rich.console import Console
from rich.table import Table

from whist.players.random_player import RandomPlayer
from whist.players.heuristic import HeuristicPlayer
from whist.simulation.runner import SimulationResult, run_games

console = Console()


def make_random_factory(seed_base: int = 0):
    counter = [seed_base]
    def factory():
        counter[0] += 1
        return RandomPlayer(random.Random(counter[0]))
    return factory


def make_heuristic_factory():
    return HeuristicPlayer


def make_ai_factory(num_samples: int = 20):
    counter = [0]
    def factory():
        from whist.players.ai.ai_player import AIPlayer
        counter[0] += 1
        return AIPlayer(player_id=1, num_samples=num_samples, rng=random.Random(counter[0] * 7))
    return factory


def run_arena(
    n_games: int = 500,
    seed: int | None = None,
    include_ai: bool = True,
) -> list[SimulationResult]:
    """Run a round-robin tournament between player types."""
    results = []

    matchups = [
        ("Random", "Random", make_random_factory(0), make_random_factory(1000)),
        ("Heuristic", "Random", make_heuristic_factory(), make_random_factory(2000)),
        ("Heuristic", "Heuristic", make_heuristic_factory(), make_heuristic_factory()),
    ]

    if include_ai:
        matchups.extend([
            ("AI (20 samples)", "Random", make_ai_factory(20), make_random_factory(3000)),
            ("AI (20 samples)", "Heuristic", make_ai_factory(20), make_heuristic_factory()),
        ])

    for p0_name, p1_name, p0_factory, p1_factory in matchups:
        console.print(f"  Running {p0_name} vs {p1_name} ({n_games} games)...")
        result = run_games(
            n_games=n_games,
            player0_factory=p0_factory,
            player1_factory=p1_factory,
            player0_name=p0_name,
            player1_name=p1_name,
            seed=seed,
        )
        results.append(result)

    return results


def print_arena_results(results: list[SimulationResult]) -> None:
    """Print tournament results as a nice table."""
    table = Table(title="Tournament Results")
    table.add_column("Player 0")
    table.add_column("Player 1")
    table.add_column("Games")
    table.add_column("P0 Wins")
    table.add_column("P1 Wins")
    table.add_column("P0 Win%")
    table.add_column("P0 Avg Tricks")
    table.add_column("Time (s)")

    for r in results:
        table.add_row(
            r.player0_type,
            r.player1_type,
            str(r.n_games),
            str(r.p0_wins),
            str(r.p1_wins),
            f"{r.p0_win_rate:.1%}",
            f"{r.p0_avg_tricks:.1f}",
            f"{r.elapsed_seconds:.1f}",
        )

    console.print(table)

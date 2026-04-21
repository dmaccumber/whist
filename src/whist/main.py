"""CLI entry point for German Whist."""

from __future__ import annotations

import argparse
import random
import sys

from rich.console import Console

from whist.core.game import Game
from whist.core.game_state import Phase
from whist.players.human import HumanPlayer
from whist.players.random_player import RandomPlayer
from whist.ui import terminal as ui


console = Console()


def play_interactive(difficulty: str = "medium", seed: int | None = None, hint: bool = False) -> None:
    """Play a game of German Whist against the AI."""
    rng = random.Random(seed)

    human = HumanPlayer(player_id=0, show_hints=hint)

    if difficulty == "easy":
        from whist.players.heuristic import HeuristicPlayer
        opponent = HeuristicPlayer()
        opponent_name = "Heuristic AI"
    elif difficulty == "hard":
        try:
            from whist.players.ai.ai_player import AIPlayer
            opponent = AIPlayer(player_id=1, num_samples=50)
            opponent_name = "Hard AI (Determinized + Minimax)"
        except ImportError:
            from whist.players.heuristic import HeuristicPlayer
            opponent = HeuristicPlayer()
            opponent_name = "Heuristic AI (fallback)"
    else:  # medium
        try:
            from whist.players.ai.ai_player import AIPlayer
            opponent = AIPlayer(player_id=1, num_samples=20)
            opponent_name = "Medium AI (Determinized + Minimax)"
        except ImportError:
            from whist.players.heuristic import HeuristicPlayer
            opponent = HeuristicPlayer()
            opponent_name = "Heuristic AI (fallback)"

    console.print()
    console.print(f"[bold blue]═══ German Whist ═══[/bold blue]")
    console.print(f"  Opponent: {opponent_name}")
    console.print(f"  You are Player 0 (non-dealer, lead first)")
    console.print()

    def on_phase_change(state):
        if state.phase == Phase.PHASE2:
            ui.display_phase_transition()

    game = Game(
        players=(human, opponent),
        rng=rng,
        on_phase_change=on_phase_change,
    )
    result = game.play()

    ui.display_game_result(result.phase2_tricks, result.winner, player_id=0)


def run_simulation(n_games: int, seed: int | None = None) -> None:
    """Run AI vs AI simulation."""
    try:
        from whist.simulation.runner import run_games
        from whist.simulation.analysis import print_summary
    except ImportError:
        console.print("[red]Simulation module not available yet.[/red]")
        return

    results = run_games(n_games, seed=seed)
    print_summary(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="German Whist card game")
    parser.add_argument(
        "--difficulty", "-d",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="AI difficulty level (default: medium)",
    )
    parser.add_argument(
        "--simulate", "-s",
        type=int,
        metavar="N",
        help="Run N simulated games instead of interactive play",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--hint",
        action="store_true",
        help="Show the AI's recommended play before each move",
    )

    args = parser.parse_args()

    if args.simulate:
        run_simulation(args.simulate, seed=args.seed)
    else:
        play_interactive(args.difficulty, seed=args.seed, hint=args.hint)


if __name__ == "__main__":
    main()

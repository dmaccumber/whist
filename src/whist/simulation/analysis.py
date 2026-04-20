"""Statistical analysis and figure generation for the report."""

from __future__ import annotations

import math
import os
from typing import Optional

from rich.console import Console
from rich.table import Table

from whist.simulation.runner import SimulationResult

console = Console()


def print_summary(results: SimulationResult) -> None:
    """Print a summary of simulation results."""
    console.print(f"\n[bold]Simulation: {results.player0_type} vs {results.player1_type}[/bold]")
    console.print(f"  Games: {results.n_games}")
    console.print(f"  {results.player0_type} wins: {results.p0_wins} ({results.p0_win_rate:.1%})")
    console.print(f"  {results.player1_type} wins: {results.p1_wins} ({results.p1_win_rate:.1%})")
    console.print(f"  Draws: {results.draws}")
    console.print(f"  Avg tricks: {results.p0_avg_tricks:.1f} vs {results.p1_avg_tricks:.1f}")
    console.print(f"  Time: {results.elapsed_seconds:.1f}s")

    # Confidence interval for P0 win rate
    p = results.p0_win_rate
    n = results.n_games
    if n > 0:
        se = math.sqrt(p * (1 - p) / n)
        ci_low = max(0, p - 1.96 * se)
        ci_high = min(1, p + 1.96 * se)
        console.print(f"  P0 win rate 95% CI: [{ci_low:.1%}, {ci_high:.1%}]")

    # Score distribution
    scores = [r.phase2_tricks[0] - r.phase2_tricks[1] for r in results.results]
    if scores:
        avg = sum(scores) / len(scores)
        var = sum((s - avg) ** 2 for s in scores) / len(scores)
        std = math.sqrt(var)
        console.print(f"  Score diff (P0-P1): mean={avg:.2f}, std={std:.2f}")


def compute_win_rate_ci(results: SimulationResult, player: int = 0) -> tuple[float, float, float]:
    """Compute win rate with 95% confidence interval.

    Returns: (win_rate, ci_low, ci_high)
    """
    n = results.n_games
    if n == 0:
        return (0.0, 0.0, 0.0)

    if player == 0:
        p = results.p0_win_rate
    else:
        p = results.p1_win_rate

    se = math.sqrt(p * (1 - p) / n) if n > 0 else 0
    return (p, max(0, p - 1.96 * se), min(1, p + 1.96 * se))


def score_distribution(results: SimulationResult) -> dict[int, int]:
    """Count games by Phase 2 trick differential (P0 - P1)."""
    dist: dict[int, int] = {}
    for r in results.results:
        diff = r.phase2_tricks[0] - r.phase2_tricks[1]
        dist[diff] = dist.get(diff, 0) + 1
    return dict(sorted(dist.items()))


def trump_suit_analysis(results: SimulationResult) -> dict:
    """Analyze win rates by trump suit."""
    from whist.core.card import Suit

    suit_stats: dict[Suit, list[int]] = {s: [0, 0] for s in Suit}
    for r in results.results:
        suit_stats[r.trump][0] += 1
        if r.winner == 0:
            suit_stats[r.trump][1] += 1

    return {
        s.name: {"games": total, "p0_wins": wins, "p0_wr": wins / total if total else 0}
        for s, (total, wins) in suit_stats.items()
    }


def generate_figures(
    results_list: list[SimulationResult],
    output_dir: str = "report/figures",
) -> None:
    """Generate matplotlib figures for the LaTeX report."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        console.print("[yellow]matplotlib not available, skipping figure generation[/yellow]")
        return

    os.makedirs(output_dir, exist_ok=True)

    # Figure 1: Win rate bar chart
    fig, ax = plt.subplots(figsize=(10, 5))
    names = [f"{r.player0_type}\nvs\n{r.player1_type}" for r in results_list]
    p0_rates = [r.p0_win_rate * 100 for r in results_list]
    p1_rates = [r.p1_win_rate * 100 for r in results_list]

    x = np.arange(len(names))
    width = 0.35
    ax.bar(x - width / 2, p0_rates, width, label='Player 0', color='steelblue')
    ax.bar(x + width / 2, p1_rates, width, label='Player 1', color='coral')
    ax.set_ylabel('Win Rate (%)')
    ax.set_title('Win Rates by Player Type Matchup')
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8)
    ax.legend()
    ax.set_ylim(0, 100)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, 'win_rates.pdf'))
    plt.close(fig)

    # Figure 2: Score distribution histogram (for first result with >100 games)
    for r in results_list:
        if r.n_games >= 100:
            fig, ax = plt.subplots(figsize=(8, 5))
            scores = [g.phase2_tricks[0] - g.phase2_tricks[1] for g in r.results]
            ax.hist(scores, bins=range(-14, 15), color='steelblue', edgecolor='black', alpha=0.7)
            ax.set_xlabel('Score Differential (P0 - P1)')
            ax.set_ylabel('Frequency')
            ax.set_title(f'Score Distribution: {r.player0_type} vs {r.player1_type}')
            ax.axvline(x=0, color='red', linestyle='--', alpha=0.5)
            fig.tight_layout()
            fig.savefig(os.path.join(output_dir, 'score_distribution.pdf'))
            plt.close(fig)
            break

    console.print(f"  Figures saved to {output_dir}/")


def export_csv(results: SimulationResult, filepath: str) -> None:
    """Export game results to CSV."""
    with open(filepath, 'w') as f:
        f.write("game,p0_tricks,p1_tricks,winner,trump,score_diff\n")
        for i, r in enumerate(results.results):
            winner_str = str(r.winner) if r.winner is not None else "draw"
            diff = r.phase2_tricks[0] - r.phase2_tricks[1]
            f.write(f"{i},{r.phase2_tricks[0]},{r.phase2_tricks[1]},{winner_str},{r.trump.name},{diff}\n")
    console.print(f"  Results exported to {filepath}")

# German Whist

A computer implementation of the two-player card game German Whist, with an AI opponent and a strategy analysis report.

I first learned this game at 11th St Bar in Manhattan and wanted to understand it more deeply -- what makes a hand strong, when to fight for the face-up card, and whether there's an optimal way to play. This project is the result of that curiosity: a playable game, a minimax-based AI, and a statistical analysis of strategy.

## The Game

German Whist is a two-player trick-taking game played with a standard 52-card deck. It has two phases:

1. **Phase 1 (Card Acquisition):** Players compete for face-up cards from a stock to build their hands. The trick winner takes the visible card; the loser takes an unknown card from underneath.
2. **Phase 2 (Trick-Taking):** Players play out their 13-card hands. Whoever wins the majority of tricks wins the game.

The strategic depth comes from Phase 1: every decision about whether to win or lose a trick shapes the hand you'll play in Phase 2.

## Playing

```bash
# Set up
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Play
python -m whist              # medium difficulty (default)
python -m whist -d easy      # heuristic-only opponent
python -m whist -d hard      # stronger AI (more sampling)
python -m whist --seed 42    # reproducible deal
```

Cards are entered by rank and suit, e.g. `AS` (Ace of Spades), `10H` (Ten of Hearts), `KD` (King of Diamonds). You can also type the number shown next to each legal play.

## AI Design

The AI uses different strategies for each phase:

- **Phase 1:** Rule-based heuristic -- win high cards (Aces, Kings, trumps), lose deliberately for low-value face-up cards.
- **Phase 2:** Alpha-beta minimax with exact solving for positions with 10 or fewer cards per player. Card counting throughout the game ensures the AI knows the opponent's exact hand entering Phase 2.

Over 500 simulated games, the AI wins 52.6% against the heuristic-only player -- a modest but consistent edge from optimal endgame play.

## Strategy Report

The `report/` directory contains a LaTeX report analyzing optimal strategy through simulation:

- [View the compiled PDF](report/main.pdf)

To recompile after changes:

```bash
make report
```

Key findings from the analysis:
- Simple heuristics (win face cards, lead aces) beat random play 93% of the time
- Trump acquisition in Phase 1 is the strongest predictor of Phase 2 success
- The non-dealer has no significant first-move advantage; the dealer may have a slight edge in skilled play
- Exact minimax in Phase 2 provides a ~3 percentage point advantage over heuristic play

## Running Simulations

```bash
python -m whist --simulate 1000    # run 1000 AI-vs-heuristic games
```

The simulation framework supports round-robin tournaments between player types and exports results to CSV and matplotlib figures.

## Tests

```bash
make test
```

## Project Structure

```
src/whist/
  core/           Game engine (cards, tricks, state, rules)
  players/        Player implementations (human, random, heuristic, AI)
  players/ai/     Minimax solver, card counter, hand evaluator
  ui/             Terminal display (Rich)
  simulation/     Game runner, arena, statistical analysis
report/           LaTeX strategy report with figures
tests/            Unit and integration tests
```

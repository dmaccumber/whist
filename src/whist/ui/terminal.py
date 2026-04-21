"""Rich-based terminal UI for German Whist."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from whist.core.card import Card, Suit
from whist.core.game_state import GameState, Observation, Phase


console = Console()

# Suit colors
_SUIT_COLORS = {
    Suit.HEARTS: "red",
    Suit.DIAMONDS: "red",
    Suit.CLUBS: "white",
    Suit.SPADES: "white",
}


def styled_card(card: Card) -> Text:
    """Return a Rich Text with the card colored by suit."""
    color = _SUIT_COLORS[card.suit]
    return Text(card.short_str(), style=f"bold {color}")


def styled_suit(suit: Suit) -> Text:
    color = _SUIT_COLORS[suit]
    return Text(f"{suit.symbol} {suit.name.capitalize()}", style=f"bold {color}")


def render_hand(cards: frozenset[Card], trump: Suit) -> Text:
    """Render a hand grouped by suit, trump suit first."""
    suit_order = [trump] + [s for s in Suit if s != trump]
    result = Text()

    for i, suit in enumerate(suit_order):
        suit_cards = sorted(
            [c for c in cards if c.suit == suit],
            key=lambda c: c.rank,
            reverse=True,
        )
        if not suit_cards:
            continue
        if i > 0 and result.plain:
            result.append("  ")

        color = _SUIT_COLORS[suit]
        is_trump = suit == trump
        prefix = "*" if is_trump else ""
        result.append(f"{prefix}{suit.symbol}: ", style=f"bold {color}")
        for j, card in enumerate(suit_cards):
            if j > 0:
                result.append(" ", style=color)
            result.append(card.rank.short, style=f"bold {color}")

    return result


def display_game_header(obs: Observation) -> None:
    """Display the game status header."""
    phase_str = "Phase 1 — Building your hand" if obs.phase == Phase.PHASE1 else "Phase 2 — Playing for tricks"

    header = Table.grid(padding=(0, 2))
    header.add_column()
    header.add_column()

    header.add_row("Phase:", phase_str)
    header.add_row("Trump:", styled_suit(obs.trump))

    if obs.phase == Phase.PHASE1:
        face_up_str = styled_card(obs.face_up) if obs.face_up else Text("(empty)")
        header.add_row("Stock:", f"{obs.stock_remaining} cards")
        header.add_row("Face-up:", face_up_str)
    else:
        my_tricks = obs.phase2_tricks[obs.i_am_player]
        opp_tricks = obs.phase2_tricks[1 - obs.i_am_player]
        header.add_row("Your tricks:", str(my_tricks))
        header.add_row("Opponent tricks:", str(opp_tricks))

    trick_num = obs.tricks_played_in_phase + 1
    total = 13
    header.add_row("Trick:", f"{trick_num} of {total}")

    console.print(Panel(header, title="[bold]German Whist[/bold]", border_style="blue"))


def display_trick_play(
    obs: Observation,
    lead_card: Optional[Card] = None,
) -> None:
    """Show what has been played in the current trick."""
    if obs.lead_card is not None:
        who = "You" if obs.leader == obs.i_am_player else "Opponent"
        console.print(f"  {who} led: ", end="")
        console.print(styled_card(obs.lead_card))


def display_hand(obs: Observation) -> None:
    """Display the player's hand."""
    console.print()
    console.print("  Your hand: ", end="")
    console.print(render_hand(obs.my_hand, obs.trump))
    console.print()


def display_legal_moves(legal_moves: list[Card], hint: Optional[Card] = None) -> None:
    """Display numbered legal moves, optionally highlighting the recommended play."""
    result = Text("  Legal plays: ")
    for i, card in enumerate(legal_moves):
        if i > 0:
            result.append(", ")
        result.append(f"[{i + 1}] ")
        result.append_text(styled_card(card))
    console.print(result)

    if hint is not None:
        console.print(f"  [italic cyan]Suggested: {hint.short_str()}[/italic cyan]")


def display_trick_result(
    lead_card: Card,
    follow_card: Card,
    winner: int,
    player_id: int,
    face_up: Optional[Card],
    face_down: Optional[Card],
    phase: Phase,
) -> None:
    """Display the result of a trick."""
    who_won = "You" if winner == player_id else "Opponent"
    console.print()
    result = Text(f"  {who_won} won the trick (")
    result.append_text(styled_card(lead_card))
    result.append(" vs ")
    result.append_text(styled_card(follow_card))
    result.append(")")
    console.print(result)

    if phase == Phase.PHASE1 and face_up is not None:
        if winner == player_id:
            took = Text("  You took: ")
            took.append_text(styled_card(face_up))
            console.print(took)
            if face_down is not None:
                console.print("  Opponent took: [dim]face-down card[/dim]")
        else:
            took = Text("  Opponent took: ")
            took.append_text(styled_card(face_up))
            console.print(took)
            if face_down is not None:
                you_took = Text("  You took: ")
                you_took.append_text(styled_card(face_down))
                console.print(you_took)

    console.print("  " + "─" * 40)


def display_phase_transition() -> None:
    """Announce transition from Phase 1 to Phase 2."""
    console.print()
    console.print(
        Panel(
            "[bold yellow]Phase 2 begins![/bold yellow]\n"
            "Now playing for tricks. Win the majority of 13 to win the game.",
            border_style="yellow",
        )
    )


def display_game_result(
    phase2_tricks: tuple[int, int],
    winner: Optional[int],
    player_id: int,
) -> None:
    """Display the final game result."""
    my_tricks = phase2_tricks[player_id]
    opp_tricks = phase2_tricks[1 - player_id]

    console.print()
    if winner == player_id:
        msg = f"[bold green]You win![/bold green] ({my_tricks}-{opp_tricks})"
    elif winner is None:
        msg = f"[bold yellow]Draw![/bold yellow] ({my_tricks}-{opp_tricks})"
    else:
        msg = f"[bold red]You lose.[/bold red] ({my_tricks}-{opp_tricks})"

    console.print(Panel(msg, title="[bold]Game Over[/bold]", border_style="bright_white"))


def prompt_card(legal_moves: list[Card]) -> Card:
    """Prompt the user to pick a card. Accepts number or card name."""
    while True:
        try:
            raw = console.input("  Your play > ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n  Game aborted.")
            raise SystemExit(0)

        if not raw:
            continue

        # Try numeric selection
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(legal_moves):
                return legal_moves[idx]
            console.print(f"  [red]Pick 1-{len(legal_moves)}.[/red]")
            continue

        # Try card name parsing
        from whist.core.card import parse_card
        card = parse_card(raw)
        if card is not None and card in legal_moves:
            return card

        console.print("  [red]Invalid. Enter a number or card name (e.g. AS, 10H, KD).[/red]")

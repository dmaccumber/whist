"""Immutable game state for German Whist, designed for AI search."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

from whist.core.card import Card, Suit
from whist.core.trick import resolve_trick


class Phase(IntEnum):
    PHASE1 = 1
    PHASE2 = 2


@dataclass(frozen=True)
class GameState:
    """Immutable snapshot of a German Whist game.

    Players are indexed 0 and 1. Player 0 is the non-dealer (leads first).
    """
    hands: tuple[frozenset[Card], frozenset[Card]]
    stock: tuple[Card, ...]       # Remaining stock cards (index 0 = top/face-up)
    trump: Suit
    phase: Phase
    leader: int                    # 0 or 1: who leads this trick
    phase2_tricks: tuple[int, int] # Tricks won by each player in Phase 2
    lead_card: Optional[Card]      # Card played by leader (None if leader hasn't played yet)
    tricks_played: int             # Total tricks played in current phase

    @staticmethod
    def initial(
        hand0: frozenset[Card],
        hand1: frozenset[Card],
        stock: tuple[Card, ...],
        trump: Suit,
    ) -> GameState:
        return GameState(
            hands=(hand0, hand1),
            stock=stock,
            trump=trump,
            phase=Phase.PHASE1,
            leader=0,  # Non-dealer leads first
            phase2_tricks=(0, 0),
            lead_card=None,
            tricks_played=0,
        )

    @property
    def face_up(self) -> Optional[Card]:
        """The face-up card on top of the stock, or None if stock is empty."""
        return self.stock[0] if self.stock else None

    @property
    def current_player(self) -> int:
        """Whose turn it is to play."""
        if self.lead_card is None:
            return self.leader
        else:
            return 1 - self.leader

    @property
    def is_terminal(self) -> bool:
        return (
            self.phase == Phase.PHASE2
            and len(self.hands[0]) == 0
            and len(self.hands[1]) == 0
        )

    @property
    def result(self) -> Optional[tuple[int, int]]:
        """Phase 2 trick scores if game is over, else None."""
        if self.is_terminal:
            return self.phase2_tricks
        return None

    @property
    def winner(self) -> Optional[int]:
        """0 or 1 for the winning player, None if not finished or draw."""
        if not self.is_terminal:
            return None
        t0, t1 = self.phase2_tricks
        if t0 > t1:
            return 0
        elif t1 > t0:
            return 1
        return None  # Draw (shouldn't happen with 13 tricks)

    def legal_moves(self) -> list[Card]:
        """Return the list of legal cards the current player can play."""
        player = self.current_player
        hand = self.hands[player]

        if self.lead_card is None:
            # Leader can play anything
            return sorted(hand)

        # Follower must follow suit if able
        led_suit = self.lead_card.suit
        in_suit = [c for c in hand if c.suit == led_suit]
        if in_suit:
            return sorted(in_suit)
        return sorted(hand)

    def play_card(self, card: Card) -> GameState:
        """Play a card and return the new state.

        If this is the leader's play, sets lead_card.
        If this is the follower's play, resolves the trick.
        """
        player = self.current_player
        new_hand = self.hands[player] - {card}
        new_hands = (
            (new_hand, self.hands[1]) if player == 0
            else (self.hands[0], new_hand)
        )

        if self.lead_card is None:
            # Leader just played
            return GameState(
                hands=new_hands,
                stock=self.stock,
                trump=self.trump,
                phase=self.phase,
                leader=self.leader,
                phase2_tricks=self.phase2_tricks,
                lead_card=card,
                tricks_played=self.tricks_played,
            )

        # Follower just played — resolve trick
        trick_winner_offset = resolve_trick(self.lead_card, card, self.trump)
        trick_winner = (self.leader + trick_winner_offset) % 2
        trick_loser = 1 - trick_winner

        new_tricks_played = self.tricks_played + 1

        if self.phase == Phase.PHASE1:
            return self._resolve_phase1_trick(
                new_hands, trick_winner, trick_loser, new_tricks_played
            )
        else:
            return self._resolve_phase2_trick(
                new_hands, trick_winner, new_tricks_played
            )

    def _resolve_phase1_trick(
        self,
        hands: tuple[frozenset[Card], frozenset[Card]],
        winner: int,
        loser: int,
        tricks_played: int,
    ) -> GameState:
        """Handle Phase 1 trick: draw from stock, possibly transition to Phase 2."""
        if len(self.stock) == 0:
            # Stock exhausted (can happen in ISMCTS determinizations) — transition to Phase 2
            return GameState(
                hands=hands,
                stock=(),
                trump=self.trump,
                phase=Phase.PHASE2,
                leader=winner,
                phase2_tricks=(0, 0),
                lead_card=None,
                tricks_played=0,
            )

        # Winner takes face-up card, loser takes next card
        face_up = self.stock[0]
        face_down = self.stock[1] if len(self.stock) > 1 else None
        new_stock = self.stock[2:]  # Remove top 2 cards from stock

        winner_hand = hands[winner] | {face_up}
        loser_hand = hands[loser] | {face_down} if face_down else hands[loser]

        new_hands = (
            (winner_hand, loser_hand) if winner == 0
            else (loser_hand, winner_hand)
        )

        # After 13 tricks in Phase 1, transition to Phase 2
        if tricks_played >= 13:
            return GameState(
                hands=new_hands,
                stock=(),
                trump=self.trump,
                phase=Phase.PHASE2,
                leader=winner,
                phase2_tricks=(0, 0),
                lead_card=None,
                tricks_played=0,
            )

        return GameState(
            hands=new_hands,
            stock=new_stock,
            trump=self.trump,
            phase=Phase.PHASE1,
            leader=winner,
            phase2_tricks=(0, 0),
            lead_card=None,
            tricks_played=tricks_played,
        )

    def _resolve_phase2_trick(
        self,
        hands: tuple[frozenset[Card], frozenset[Card]],
        winner: int,
        tricks_played: int,
    ) -> GameState:
        """Handle Phase 2 trick: just count it."""
        t0, t1 = self.phase2_tricks
        if winner == 0:
            new_tricks = (t0 + 1, t1)
        else:
            new_tricks = (t0, t1 + 1)

        return GameState(
            hands=hands,
            stock=(),
            trump=self.trump,
            phase=Phase.PHASE2,
            leader=winner,
            phase2_tricks=new_tricks,
            lead_card=None,
            tricks_played=tricks_played,
        )


@dataclass(frozen=True)
class Observation:
    """What a player can legally see about the game state.

    This enforces the information barrier — players never see
    opponent's hand or face-down stock cards.
    """
    my_hand: frozenset[Card]
    trump: Suit
    phase: Phase
    face_up: Optional[Card]       # Top of stock (None in Phase 2)
    stock_remaining: int           # How many cards left in stock
    leader: int                    # Who leads this trick
    i_am_player: int               # Which player am I (0 or 1)
    lead_card: Optional[Card]      # Card led this trick (None if I'm leading)
    phase2_tricks: tuple[int, int] # Phase 2 scores
    tricks_played_in_phase: int    # Tricks played so far in current phase

    @staticmethod
    def from_state(state: GameState, player: int) -> Observation:
        return Observation(
            my_hand=state.hands[player],
            trump=state.trump,
            phase=state.phase,
            face_up=state.face_up,
            stock_remaining=len(state.stock),
            leader=state.leader,
            i_am_player=player,
            lead_card=state.lead_card,
            phase2_tricks=state.phase2_tricks,
            tricks_played_in_phase=state.tricks_played,
        )

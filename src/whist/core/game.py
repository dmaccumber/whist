"""Game controller for German Whist."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional, Protocol

from whist.core.card import Card, Suit
from whist.core.deck import deal
from whist.core.game_state import GameState, Observation, Phase


class Player(Protocol):
    """Interface that all players must implement."""

    def choose_card(self, observation: Observation, legal_moves: list[Card]) -> Card:
        """Choose a card to play from the legal moves."""
        ...

    def notify_trick_result(
        self,
        lead_card: Card,
        follow_card: Card,
        winner: int,
        face_up_taken: Optional[Card],
        face_down_taken: Optional[Card],
        phase: Phase,
    ) -> None:
        """Called after each trick so players can track cards."""
        ...


@dataclass
class TrickRecord:
    """Record of a single trick."""
    trick_num: int
    phase: Phase
    leader: int
    lead_card: Card
    follow_card: Card
    winner: int
    face_up_card: Optional[Card] = None  # Face-up card available (Phase 1)


@dataclass
class GameResult:
    """Complete result of a German Whist game."""
    phase2_tricks: tuple[int, int]  # (player0, player1)
    winner: Optional[int]           # 0, 1, or None for draw
    trump: Suit
    tricks: list[TrickRecord] = field(default_factory=list)

    @property
    def score_diff(self) -> int:
        """Absolute difference in Phase 2 tricks."""
        return abs(self.phase2_tricks[0] - self.phase2_tricks[1])


class Game:
    """Orchestrates a full German Whist game between two players."""

    def __init__(
        self,
        players: tuple[Player, Player],
        rng: random.Random | None = None,
        on_trick: Optional[callable] = None,
        on_phase_change: Optional[callable] = None,
    ):
        self.players = players
        self.rng = rng or random.Random()
        self.on_trick = on_trick
        self.on_phase_change = on_phase_change
        self.state: Optional[GameState] = None
        self.tricks: list[TrickRecord] = []

    def play(self) -> GameResult:
        """Play a complete game and return the result."""
        d = deal(self.rng)
        self.state = GameState.initial(
            hand0=frozenset(d.hand0),
            hand1=frozenset(d.hand1),
            stock=tuple(d.stock),
            trump=d.trump,
        )
        self.tricks = []

        while not self.state.is_terminal:
            self._play_trick()

        return GameResult(
            phase2_tricks=self.state.phase2_tricks,
            winner=self.state.winner,
            trump=self.state.trump,
            tricks=self.tricks,
        )

    def _play_trick(self) -> None:
        """Play one complete trick (leader + follower)."""
        state = self.state
        old_phase = state.phase
        face_up = state.face_up
        face_down = state.stock[1] if len(state.stock) > 1 else None

        # Leader plays
        leader = state.leader
        leader_obs = Observation.from_state(state, leader)
        leader_moves = state.legal_moves()
        lead_card = self.players[leader].choose_card(leader_obs, leader_moves)
        assert lead_card in leader_moves, f"Illegal move: {lead_card}"
        state = state.play_card(lead_card)

        # Follower plays
        follower = state.current_player
        follower_obs = Observation.from_state(state, follower)
        follower_moves = state.legal_moves()
        follow_card = self.players[follower].choose_card(follower_obs, follower_moves)
        assert follow_card in follower_moves, f"Illegal move: {follow_card}"
        state = state.play_card(follow_card)

        # Determine who won
        winner = state.leader  # After resolving, leader is set to trick winner

        trick = TrickRecord(
            trick_num=len(self.tricks),
            phase=old_phase,
            leader=leader,
            lead_card=lead_card,
            follow_card=follow_card,
            winner=winner,
            face_up_card=face_up,
        )
        self.tricks.append(trick)

        # Notify players
        for p in self.players:
            p.notify_trick_result(
                lead_card, follow_card, winner, face_up, face_down, old_phase,
            )

        if self.on_trick:
            self.on_trick(trick, state)

        if old_phase != state.phase and self.on_phase_change:
            self.on_phase_change(state)

        self.state = state

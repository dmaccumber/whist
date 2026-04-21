"""Human player — interacts via terminal UI."""

from __future__ import annotations

from typing import Optional

from whist.core.card import Card
from whist.core.game_state import Observation, Phase
from whist.players.base import BasePlayer
from whist.ui import terminal as ui


class HumanPlayer(BasePlayer):
    def __init__(self, player_id: int = 0, show_hints: bool = False):
        self.player_id = player_id
        self.show_hints = show_hints
        self._advisor = None
        if show_hints:
            from whist.players.ai.ai_player import AIPlayer
            self._advisor = AIPlayer(player_id=player_id)

    def choose_card(self, observation: Observation, legal_moves: list[Card]) -> Card:
        ui.display_game_header(observation)
        ui.display_trick_play(observation)
        ui.display_hand(observation)

        hint = None
        if self.show_hints and self._advisor and len(legal_moves) > 1:
            hint = self._advisor.choose_card(observation, legal_moves)

        ui.display_legal_moves(legal_moves, hint=hint)
        return ui.prompt_card(legal_moves)

    def notify_trick_result(
        self,
        lead_card: Card,
        follow_card: Card,
        winner: int,
        face_up_taken: Optional[Card],
        face_down_taken: Optional[Card],
        phase: Phase,
    ) -> None:
        ui.display_trick_result(
            lead_card, follow_card, winner,
            self.player_id, face_up_taken, face_down_taken, phase,
        )
        if self._advisor is not None:
            self._advisor.notify_trick_result(
                lead_card, follow_card, winner,
                face_up_taken, face_down_taken, phase,
            )

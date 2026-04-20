"""Base player class with default no-op notifications."""

from __future__ import annotations

from typing import Optional

from whist.core.card import Card
from whist.core.game_state import Observation, Phase


class BasePlayer:
    """Base class for all players. Subclasses must override choose_card."""

    def choose_card(self, observation: Observation, legal_moves: list[Card]) -> Card:
        raise NotImplementedError

    def notify_trick_result(
        self,
        lead_card: Card,
        follow_card: Card,
        winner: int,
        face_up_taken: Optional[Card],
        phase: Phase,
    ) -> None:
        pass

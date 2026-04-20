"""Random player — picks uniformly from legal moves."""

from __future__ import annotations

import random

from whist.core.card import Card
from whist.core.game_state import Observation
from whist.players.base import BasePlayer


class RandomPlayer(BasePlayer):
    def __init__(self, rng: random.Random | None = None):
        self.rng = rng or random.Random()

    def choose_card(self, observation: Observation, legal_moves: list[Card]) -> Card:
        return self.rng.choice(legal_moves)

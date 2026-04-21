"""Unified AI player for German Whist.

Phase 1: Uses determinized evaluation (sample opponent hands, evaluate moves)
Phase 2: Uses exact minimax with alpha-beta pruning
"""

from __future__ import annotations

import random
from typing import Optional

from whist.core.card import Card
from whist.core.game_state import Observation, Phase
from whist.players.base import BasePlayer
from whist.players.ai.card_counter import CardCounter
from whist.players.ai.ismcts import determinized_choose
from whist.players.ai.minimax import solve_phase2


class AIPlayer(BasePlayer):
    """Strong AI player using determinized evaluation + Minimax."""

    def __init__(
        self,
        player_id: int = 1,
        num_samples: int = 30,
        rng: random.Random | None = None,
    ):
        self.player_id = player_id
        self.num_samples = num_samples
        self.rng = rng or random.Random()
        self.counter: Optional[CardCounter] = None
        self._initialized = False

    def _ensure_init(self, obs: Observation) -> None:
        if not self._initialized:
            self.counter = CardCounter(obs.my_hand, obs.trump, self.player_id)
            if obs.face_up is not None:
                self.counter.observe_face_up(obs.face_up)
            self._initialized = True

    def choose_card(self, obs: Observation, legal_moves: list[Card]) -> Card:
        self._ensure_init(obs)

        self.counter.update_my_hand(obs.my_hand)
        if obs.face_up is not None:
            self.counter.observe_face_up(obs.face_up)

        if len(legal_moves) == 1:
            return legal_moves[0]

        if obs.phase == Phase.PHASE1:
            return self._phase1_choose(obs, legal_moves)
        else:
            return self._phase2_choose(obs, legal_moves)

    def _phase1_choose(self, obs: Observation, legal_moves: list[Card]) -> Card:
        """Use heuristic rules for Phase 1 card acquisition."""
        from whist.players.heuristic import HeuristicPlayer
        return HeuristicPlayer()._phase1_play(obs, legal_moves)

    def _phase2_choose(self, obs: Observation, legal_moves: list[Card]) -> Card:
        """Use exact minimax for Phase 2."""
        if self.counter.phase != Phase.PHASE2:
            self.counter.transition_to_phase2()

        opp_hand = self.counter.get_opponent_hand_phase2()
        my_hand = frozenset(obs.my_hand)

        if self.player_id == 0:
            hands = (my_hand, opp_hand)
        else:
            hands = (opp_hand, my_hand)

        score, best_card = solve_phase2(
            hands, obs.trump, obs.leader, obs.lead_card,
        )

        if best_card is not None and best_card in legal_moves:
            return best_card

        return legal_moves[0]

    def notify_trick_result(
        self,
        lead_card: Card,
        follow_card: Card,
        winner: int,
        face_up_taken: Optional[Card],
        face_down_taken: Optional[Card],
        phase: Phase,
    ) -> None:
        if self.counter is not None:
            self.counter.observe_trick(
                lead_card, follow_card, winner, face_up_taken, phase,
            )

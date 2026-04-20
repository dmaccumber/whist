"""Rule-based heuristic player for German Whist.

Phase 1: Decides whether to win or lose based on the face-up card's value.
Phase 2: Plays a simple trick-taking strategy.
"""

from __future__ import annotations

from typing import Optional

from whist.core.card import Card, Rank, Suit
from whist.core.game_state import Observation, Phase
from whist.players.base import BasePlayer


class HeuristicPlayer(BasePlayer):
    """Heuristic player that uses simple rules for both phases."""

    def choose_card(self, obs: Observation, legal_moves: list[Card]) -> Card:
        if obs.phase == Phase.PHASE1:
            return self._phase1_play(obs, legal_moves)
        else:
            return self._phase2_play(obs, legal_moves)

    def _phase1_play(self, obs: Observation, legal_moves: list[Card]) -> Card:
        """Phase 1: Try to win good face-up cards, lose bad ones."""
        face_up = obs.face_up
        want_to_win = self._should_win_face_up(face_up, obs)

        if obs.lead_card is None:
            # We are leading
            return self._phase1_lead(obs, legal_moves, want_to_win)
        else:
            # We are following
            return self._phase1_follow(obs, legal_moves, want_to_win)

    def _should_win_face_up(self, face_up: Optional[Card], obs: Observation) -> bool:
        """Decide if the face-up card is worth winning."""
        if face_up is None:
            return True

        # Always want aces and kings
        if face_up.rank >= Rank.KING:
            return True

        # Want trump cards (especially high ones)
        if face_up.suit == obs.trump:
            return face_up.rank >= Rank.SEVEN

        # Want queens and jacks moderately
        if face_up.rank >= Rank.JACK:
            return True

        # Low cards: generally not worth fighting for
        return False

    def _phase1_lead(self, obs: Observation, legal_moves: list[Card], want_win: bool) -> Card:
        """Leading in Phase 1."""
        if want_win:
            # Lead from a strong suit to likely win
            # Lead the highest card in the suit we're strongest in
            best = None
            best_strength = -1
            for card in legal_moves:
                suit_cards = [c for c in obs.my_hand if c.suit == card.suit]
                strength = card.rank.value + len(suit_cards) * 2
                if card.suit == obs.trump:
                    strength += 5
                if strength > best_strength:
                    best_strength = strength
                    best = card
            return best
        else:
            # Lead low to try to lose
            return self._play_lowest(legal_moves, obs.trump)

    def _phase1_follow(self, obs: Observation, legal_moves: list[Card], want_win: bool) -> Card:
        """Following in Phase 1."""
        lead = obs.lead_card
        assert lead is not None

        if want_win:
            # Try to win cheaply
            return self._play_cheapest_winner(legal_moves, lead, obs.trump)
        else:
            # Try to lose
            return self._play_lowest(legal_moves, obs.trump)

    def _phase2_play(self, obs: Observation, legal_moves: list[Card]) -> Card:
        """Phase 2: standard trick-taking strategy."""
        if obs.lead_card is None:
            return self._phase2_lead(obs, legal_moves)
        else:
            return self._phase2_follow(obs, legal_moves)

    def _phase2_lead(self, obs: Observation, legal_moves: list[Card]) -> Card:
        """Leading in Phase 2: lead winners, then long suits."""
        # Lead aces first
        aces = [c for c in legal_moves if c.rank == Rank.ACE]
        if aces:
            # Prefer non-trump aces
            non_trump = [c for c in aces if c.suit != obs.trump]
            return non_trump[0] if non_trump else aces[0]

        # Lead from longest non-trump suit (to establish it)
        suits: dict[Suit, list[Card]] = {}
        for c in obs.my_hand:
            suits.setdefault(c.suit, []).append(c)

        best_suit = None
        best_len = 0
        for suit, cards in suits.items():
            if suit == obs.trump:
                continue
            if len(cards) > best_len:
                best_len = len(cards)
                best_suit = suit

        if best_suit is not None:
            suit_legal = [c for c in legal_moves if c.suit == best_suit]
            if suit_legal:
                # Lead highest in the suit
                return max(suit_legal, key=lambda c: c.rank)

        # Fall back to highest card
        return max(legal_moves, key=lambda c: c.rank)

    def _phase2_follow(self, obs: Observation, legal_moves: list[Card]) -> Card:
        """Following in Phase 2: win if cheap, duck if expensive."""
        return self._play_cheapest_winner(legal_moves, obs.lead_card, obs.trump)

    def _play_cheapest_winner(self, legal_moves: list[Card], lead: Card, trump: Suit) -> Card:
        """Play the cheapest card that wins the trick, or the lowest loser."""
        winners = []
        losers = []

        for card in legal_moves:
            if self._would_win(card, lead, trump):
                winners.append(card)
            else:
                losers.append(card)

        if winners:
            # Play the cheapest winner
            return min(winners, key=lambda c: c.rank)
        # Can't win: dump the lowest card
        return self._play_lowest(losers or legal_moves, trump)

    def _play_lowest(self, cards: list[Card], trump: Suit) -> Card:
        """Play the lowest value card, preferring non-trumps."""
        non_trump = [c for c in cards if c.suit != trump]
        pool = non_trump if non_trump else cards
        return min(pool, key=lambda c: c.rank)

    @staticmethod
    def _would_win(card: Card, lead: Card, trump: Suit) -> bool:
        """Would playing this card win against the lead card?"""
        if card.suit == lead.suit:
            return card.rank > lead.rank
        elif card.suit == trump:
            return True
        return False

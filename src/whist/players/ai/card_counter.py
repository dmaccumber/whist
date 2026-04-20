"""Card counter — tracks known and unknown cards throughout a game.

This allows the AI to maintain an accurate picture of what cards
could be in the opponent's hand and in the stock.
"""

from __future__ import annotations

from typing import Optional

from whist.core.card import Card, FULL_DECK, Suit
from whist.core.game_state import Phase


class CardCounter:
    """Tracks cards seen throughout a German Whist game."""

    def __init__(self, my_hand: frozenset[Card], trump: Suit, player_id: int):
        self.player_id = player_id
        self.trump = trump

        # Cards I definitely have
        self.my_hand: set[Card] = set(my_hand)

        # Cards I've seen (played, taken face-up, in my hand)
        self.seen: set[Card] = set(my_hand)

        # Cards that have been played (removed from game)
        self.played: set[Card] = set()

        # Face-up cards I've observed (includes ones taken by either player)
        self.face_up_seen: set[Card] = set()

        # Cards the opponent has definitely taken face-up
        self.opponent_known_cards: set[Card] = set()

        # Phase tracking
        self.phase = Phase.PHASE1

    @property
    def unknown_cards(self) -> set[Card]:
        """Cards whose location I don't know."""
        return FULL_DECK - self.seen

    @property
    def opponent_possible_cards(self) -> set[Card]:
        """Cards the opponent could have.

        In Phase 1: unknown cards + cards they took face-up
        In Phase 2: everything not in my hand and not played
        """
        if self.phase == Phase.PHASE2:
            return FULL_DECK - self.my_hand - self.played
        return self.unknown_cards | self.opponent_known_cards

    def observe_face_up(self, card: Card) -> None:
        """Observe the face-up card on the stock."""
        self.seen.add(card)
        self.face_up_seen.add(card)

    def observe_trick(
        self,
        lead_card: Card,
        follow_card: Card,
        winner: int,
        face_up: Optional[Card],
        phase: Phase,
    ) -> None:
        """Update tracking after a trick is played."""
        self.seen.add(lead_card)
        self.seen.add(follow_card)
        self.played.add(lead_card)
        self.played.add(follow_card)

        # Remove played cards from my hand
        self.my_hand.discard(lead_card)
        self.my_hand.discard(follow_card)

        if phase == Phase.PHASE1 and face_up is not None:
            self.seen.add(face_up)
            if winner == self.player_id:
                # I won — I take the face-up card
                self.my_hand.add(face_up)
            else:
                # Opponent won — they take the face-up card
                self.opponent_known_cards.add(face_up)
                # I get the face-down card (I'll see it in my hand next turn)

    def update_my_hand(self, new_hand: frozenset[Card]) -> None:
        """Update my hand (e.g., after receiving a face-down card)."""
        for card in new_hand:
            self.my_hand.add(card)
            self.seen.add(card)

    def transition_to_phase2(self) -> None:
        """Called when Phase 2 begins. At this point we can deduce the opponent's hand."""
        self.phase = Phase.PHASE2
        # Everything not in my hand and not played must be in opponent's hand
        opponent_hand = FULL_DECK - frozenset(self.my_hand) - self.played
        self.opponent_known_cards = opponent_hand
        self.seen = set(FULL_DECK)  # We now know everything

    def get_opponent_hand_phase2(self) -> frozenset[Card]:
        """In Phase 2, return the exact opponent hand."""
        return frozenset(FULL_DECK - frozenset(self.my_hand) - self.played)

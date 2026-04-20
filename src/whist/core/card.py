"""Card, Suit, and Rank types for German Whist."""

from __future__ import annotations

from enum import IntEnum
from functools import total_ordering


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3

    @property
    def symbol(self) -> str:
        return _SUIT_SYMBOLS[self]

    @property
    def name_str(self) -> str:
        return self.name.capitalize()

    def __repr__(self) -> str:
        return f"Suit.{self.name}"


_SUIT_SYMBOLS = {
    Suit.CLUBS: "\u2663",
    Suit.DIAMONDS: "\u2666",
    Suit.HEARTS: "\u2665",
    Suit.SPADES: "\u2660",
}

SUIT_FROM_CHAR = {
    "C": Suit.CLUBS, "c": Suit.CLUBS,
    "D": Suit.DIAMONDS, "d": Suit.DIAMONDS,
    "H": Suit.HEARTS, "h": Suit.HEARTS,
    "S": Suit.SPADES, "s": Suit.SPADES,
}


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

    @property
    def short(self) -> str:
        return _RANK_SHORT[self]

    def __repr__(self) -> str:
        return f"Rank.{self.name}"


_RANK_SHORT = {
    Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4", Rank.FIVE: "5",
    Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8", Rank.NINE: "9",
    Rank.TEN: "10", Rank.JACK: "J", Rank.QUEEN: "Q", Rank.KING: "K",
    Rank.ACE: "A",
}

RANK_FROM_CHAR = {v: k for k, v in _RANK_SHORT.items()}
RANK_FROM_CHAR.update({
    "a": Rank.ACE, "k": Rank.KING, "q": Rank.QUEEN, "j": Rank.JACK,
    "t": Rank.TEN, "T": Rank.TEN,
})


@total_ordering
class Card:
    """Immutable card with integer encoding for fast AI operations.

    Internal encoding: id = rank_index * 4 + suit  (0..51)
    where rank_index = rank.value - 2  (0..12)
    """

    __slots__ = ("_id",)

    def __init__(self, rank: Rank, suit: Suit) -> None:
        object.__setattr__(self, "_id", (int(rank) - 2) * 4 + int(suit))

    @classmethod
    def from_id(cls, card_id: int) -> Card:
        obj = object.__new__(cls)
        object.__setattr__(obj, "_id", card_id)
        return obj

    @property
    def id(self) -> int:
        return self._id

    @property
    def rank(self) -> Rank:
        return Rank((self._id >> 2) + 2)

    @property
    def suit(self) -> Suit:
        return Suit(self._id & 3)

    @property
    def rank_index(self) -> int:
        return self._id >> 2

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Card):
            return self._id == other._id
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Card):
            return self._id < other._id
        return NotImplemented

    def __hash__(self) -> int:
        return self._id

    def __repr__(self) -> str:
        return f"{self.rank.short}{self.suit.symbol}"

    def short_str(self) -> str:
        return f"{self.rank.short}{self.suit.symbol}"


# Pre-built lookup: ALL_CARDS[id] -> Card
ALL_CARDS: list[Card] = [Card.from_id(i) for i in range(52)]

FULL_DECK: frozenset[Card] = frozenset(ALL_CARDS)


def parse_card(text: str) -> Card | None:
    """Parse user input like 'AS', 'ah', '10H', 'KD' into a Card."""
    text = text.strip()
    if not text:
        return None
    # Try to split into rank + suit
    if len(text) >= 2:
        suit_char = text[-1]
        rank_str = text[:-1]
        suit = SUIT_FROM_CHAR.get(suit_char)
        rank = RANK_FROM_CHAR.get(rank_str)
        if suit is not None and rank is not None:
            return Card(rank, suit)
    return None

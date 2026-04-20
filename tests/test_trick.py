"""Tests for trick resolution."""

from whist.core.card import Card, Suit, Rank
from whist.core.trick import resolve_trick


def test_same_suit_higher_wins():
    lead = Card(Rank.KING, Suit.HEARTS)
    follow = Card(Rank.ACE, Suit.HEARTS)
    assert resolve_trick(lead, follow, Suit.SPADES) == 1  # Follower wins


def test_same_suit_lower_loses():
    lead = Card(Rank.ACE, Suit.HEARTS)
    follow = Card(Rank.TWO, Suit.HEARTS)
    assert resolve_trick(lead, follow, Suit.SPADES) == 0  # Leader wins


def test_trump_beats_non_trump():
    lead = Card(Rank.ACE, Suit.HEARTS)
    follow = Card(Rank.TWO, Suit.SPADES)
    assert resolve_trick(lead, follow, Suit.SPADES) == 1  # Follower trumps


def test_off_suit_non_trump_loses():
    lead = Card(Rank.TWO, Suit.HEARTS)
    follow = Card(Rank.ACE, Suit.CLUBS)
    assert resolve_trick(lead, follow, Suit.SPADES) == 0  # Leader wins (off-suit)


def test_low_trump_beats_high_non_trump():
    lead = Card(Rank.ACE, Suit.DIAMONDS)
    follow = Card(Rank.TWO, Suit.HEARTS)
    assert resolve_trick(lead, follow, Suit.HEARTS) == 1  # 2 of trump beats A


def test_same_trump_suit():
    lead = Card(Rank.JACK, Suit.SPADES)
    follow = Card(Rank.QUEEN, Suit.SPADES)
    assert resolve_trick(lead, follow, Suit.SPADES) == 1  # Higher trump wins


def test_leader_wins_with_trump_lead():
    lead = Card(Rank.ACE, Suit.SPADES)
    follow = Card(Rank.KING, Suit.HEARTS)
    assert resolve_trick(lead, follow, Suit.SPADES) == 0  # Leader's trump, follower off-suit

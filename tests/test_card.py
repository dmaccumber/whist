"""Tests for card, suit, and rank types."""

from whist.core.card import Card, Suit, Rank, ALL_CARDS, FULL_DECK, parse_card


def test_card_creation():
    c = Card(Rank.ACE, Suit.SPADES)
    assert c.rank == Rank.ACE
    assert c.suit == Suit.SPADES


def test_card_from_id_roundtrip():
    for card in ALL_CARDS:
        reconstructed = Card.from_id(card.id)
        assert reconstructed == card
        assert reconstructed.rank == card.rank
        assert reconstructed.suit == card.suit


def test_card_ids_unique():
    ids = [c.id for c in ALL_CARDS]
    assert len(set(ids)) == 52
    assert min(ids) == 0
    assert max(ids) == 51


def test_card_ordering():
    two_clubs = Card(Rank.TWO, Suit.CLUBS)
    ace_spades = Card(Rank.ACE, Suit.SPADES)
    assert two_clubs < ace_spades


def test_card_equality():
    c1 = Card(Rank.KING, Suit.HEARTS)
    c2 = Card(Rank.KING, Suit.HEARTS)
    assert c1 == c2
    assert hash(c1) == hash(c2)


def test_card_inequality():
    c1 = Card(Rank.KING, Suit.HEARTS)
    c2 = Card(Rank.KING, Suit.DIAMONDS)
    assert c1 != c2


def test_full_deck():
    assert len(FULL_DECK) == 52
    assert len(ALL_CARDS) == 52


def test_parse_card():
    assert parse_card("AS") == Card(Rank.ACE, Suit.SPADES)
    assert parse_card("10H") == Card(Rank.TEN, Suit.HEARTS)
    assert parse_card("2c") == Card(Rank.TWO, Suit.CLUBS)
    assert parse_card("KD") == Card(Rank.KING, Suit.DIAMONDS)
    assert parse_card("JH") == Card(Rank.JACK, Suit.HEARTS)
    assert parse_card("QS") == Card(Rank.QUEEN, Suit.SPADES)


def test_parse_card_invalid():
    assert parse_card("") is None
    assert parse_card("X") is None
    assert parse_card("ZZ") is None


def test_suit_symbols():
    assert Suit.HEARTS.symbol == "\u2665"
    assert Suit.SPADES.symbol == "\u2660"
    assert Suit.DIAMONDS.symbol == "\u2666"
    assert Suit.CLUBS.symbol == "\u2663"


def test_rank_short():
    assert Rank.ACE.short == "A"
    assert Rank.TEN.short == "10"
    assert Rank.TWO.short == "2"
    assert Rank.KING.short == "K"

import pytest
from django.test import TestCase
from todos.poker_utils import (
    Card, SUITS, RANKS, create_deck, deal_cards,
    serialize_cards, deserialize_cards, evaluate_hand,
    check_straight, check_flush
)

class TestPokerUtils(TestCase):
    def test_create_deck(self):
        """Test creating a new deck of cards"""
        deck = create_deck()
        self.assertEqual(len(deck), 52)
        # Check all combinations exist
        for suit in SUITS:
            for rank in RANKS:
                self.assertTrue(
                    any(card.suit == suit and card.rank == rank for card in deck)
                )

    def test_deal_cards(self):
        """Test dealing cards from deck"""
        deck = create_deck()
        initial_len = len(deck)
        dealt = deal_cards(deck, 2)
        self.assertEqual(len(dealt), 2)
        self.assertEqual(len(deck), initial_len - 2)
        
        # Test dealing more cards than in deck
        deck = [Card('A', '♠')]
        dealt = deal_cards(deck, 2)
        self.assertEqual(len(dealt), 1)
        self.assertEqual(len(deck), 0)

    def test_serialize_deserialize_cards(self):
        """Test card serialization and deserialization"""
        original_cards = [Card('A', '♠'), Card('K', '♥')]
        serialized = serialize_cards(original_cards)
        deserialized = deserialize_cards(serialized)
    
        self.assertEqual(len(deserialized), len(original_cards))
        for orig, des in zip(original_cards, deserialized):
            self.assertEqual(orig.rank, des.rank)
            self.assertEqual(orig.suit, des.suit)

    def test_evaluate_hand(self):
        """Test poker hand evaluation"""
        # Test royal flush
        royal_flush = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
            Card('J', '♠'), Card('10', '♠')
        ]
        hand_name, best_cards = evaluate_hand(royal_flush[:2], royal_flush[2:])
        self.assertEqual(hand_name, 'Straight Flush')
        
        # Test four of a kind
        four_kind = [
            Card('A', '♠'), Card('A', '♥'), Card('A', '♦'),
            Card('A', '♣'), Card('K', '♠')
        ]
        hand_name, best_cards = evaluate_hand(four_kind[:2], four_kind[2:])
        self.assertEqual(hand_name, 'Four of a Kind')
    
        # Test full house
        full_house = [
            Card('A', '♠'), Card('A', '♥'), Card('A', '♦'),
            Card('K', '♣'), Card('K', '♠')
        ]
        hand_name, best_cards = evaluate_hand(full_house[:2], full_house[2:])
        self.assertEqual(hand_name, 'Full House')

    def test_check_straight(self):
        """Test straight detection"""
        straight = [
            Card('9', '♠'), Card('8', '♥'), Card('7', '♦'),
            Card('6', '♣'), Card('5', '♠')
        ]
        result = check_straight(straight)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 5)

    def test_check_flush(self):
        """Test flush detection"""
        flush = [
            Card('A', '♠'), Card('K', '♠'), Card('Q', '♠'),
            Card('J', '♠'), Card('9', '♠')
        ]
        result = check_flush(flush)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 5)
        self.assertTrue(all(card.suit == '♠' for card in result))

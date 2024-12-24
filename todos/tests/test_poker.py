from django.test import TestCase
from todos.poker_utils import (
    Card, create_deck, deal_cards, serialize_cards, 
    deserialize_cards, evaluate_hand
)

class TestPokerUtils(TestCase):
    """Test suite for poker utility functions"""

    def test_create_deck(self):
        """Test deck creation returns 52 unique cards"""
        deck = create_deck()
        self.assertEqual(len(deck), 52)
        # Check uniqueness
        card_strs = [str(card) for card in deck]
        self.assertEqual(len(set(card_strs)), 52)

    def test_deal_cards(self):
        """Test dealing cards from deck"""
        deck = create_deck()
        initial_size = len(deck)
        dealt = deal_cards(deck, 2)
        self.assertEqual(len(dealt), 2)
        self.assertEqual(len(deck), initial_size - 2)

    def test_serialize_deserialize_cards(self):
        """Test card serialization and deserialization"""
        original_cards = [Card('A', '♠'), Card('K', '♥')]
        serialized = serialize_cards(original_cards)
        deserialized = deserialize_cards(serialized)
        self.assertEqual(len(deserialized), 2)
        self.assertEqual(str(deserialized[0]), 'A♠')
        self.assertEqual(str(deserialized[1]), 'K♥')

    def test_evaluate_hand_straight_flush(self):
        """Test straight flush detection"""
        hole_cards = [Card('9', '♠'), Card('10', '♠')]
        community = [
            Card('J', '♠'), Card('Q', '♠'), Card('K', '♠'),
            Card('2', '♥'), Card('3', '♥')
        ]
        hand_name, best_cards = evaluate_hand(hole_cards, community)
        self.assertEqual(hand_name, 'Straight Flush')
        self.assertEqual(len(best_cards), 5)

    def test_evaluate_hand_four_kind(self):
        """Test four of a kind detection"""
        hole_cards = [Card('A', '♠'), Card('A', '♥')]
        community = [
            Card('A', '♦'), Card('A', '♣'), Card('K', '♠'),
            Card('2', '♥'), Card('3', '♥')
        ]
        hand_name, best_cards = evaluate_hand(hole_cards, community)
        self.assertEqual(hand_name, 'Four of a Kind')
        self.assertEqual(len(best_cards), 5)

    def test_evaluate_hand_full_house(self):
        """Test full house detection"""
        hole_cards = [Card('K', '♠'), Card('K', '♥')]
        community = [
            Card('K', '♦'), Card('A', '♣'), Card('A', '♠'),
            Card('2', '♥'), Card('3', '♥')
        ]
        hand_name, best_cards = evaluate_hand(hole_cards, community)
        self.assertEqual(hand_name, 'Full House')
        self.assertEqual(len(best_cards), 5)

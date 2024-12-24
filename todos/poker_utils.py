import random
from typing import List, Tuple, Optional

# Card constants
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit
        
    def __str__(self):
        return f"{self.rank}{self.suit}"
        
    def __repr__(self):
        return self.__str__()

def create_deck() -> List[Card]:
    """Create a new deck of 52 cards"""
    return [Card(rank, suit) for suit in SUITS for rank in RANKS]

def deal_cards(deck: List[Card], num_cards: int) -> List[Card]:
    """Deal specified number of cards from deck"""
    dealt_cards = []
    for _ in range(num_cards):
        if len(deck) > 0:
            dealt_cards.append(deck.pop())
    return dealt_cards

def serialize_cards(cards: List[Card]) -> str:
    """Convert list of cards to string format for storage"""
    return ','.join(str(card) for card in cards)

def deserialize_cards(cards_str: str) -> List[Card]:
    """Convert string format back to list of Card objects"""
    if not cards_str:
        return []
    cards = []
    for card_str in cards_str.split(','):
        if len(card_str) >= 2:
            rank = card_str[:-1]
            suit = card_str[-1]
            cards.append(Card(rank, suit))
    return cards

def evaluate_hand(hole_cards: List[Card], community_cards: List[Card]) -> Tuple[str, List[Card]]:
    """
    Evaluate the best 5-card poker hand from hole cards and community cards.
    Returns tuple of (hand_name, best_five_cards)
    """
    all_cards = hole_cards + community_cards
    
    # Check for straight flush
    straight_flush = check_straight_flush(all_cards)
    if straight_flush:
        return ('Straight Flush', straight_flush)
        
    # Check for four of a kind
    four_kind = check_four_of_kind(all_cards)
    if four_kind:
        return ('Four of a Kind', four_kind)
    
    # Check for full house
    full_house = check_full_house(all_cards)
    if full_house:
        return ('Full House', full_house)
        
    # Check for flush
    flush = check_flush(all_cards)
    if flush:
        return ('Flush', flush)
        
    # Check for straight
    straight = check_straight(all_cards)
    if straight:
        return ('Straight', straight)
        
    # Check for three of a kind
    three_kind = check_three_of_kind(all_cards)
    if three_kind:
        return ('Three of a Kind', three_kind)
        
    # Check for two pair
    two_pair = check_two_pair(all_cards)
    if two_pair:
        return ('Two Pair', two_pair)
        
    # Check for pair
    pair = check_pair(all_cards)
    if pair:
        return ('Pair', pair)
        
    # High card
    high_cards = sorted(all_cards, key=lambda x: RANKS.index(x.rank), reverse=True)[:5]
    return ('High Card', high_cards)

def check_straight_flush(cards: List[Card]) -> Optional[List[Card]]:
    """Check for straight flush"""
    for suit in SUITS:
        suited_cards = [card for card in cards if card.suit == suit]
        if len(suited_cards) >= 5:
            straight = check_straight(suited_cards)
            if straight:
                return straight
    return None

def check_four_of_kind(cards: List[Card]) -> Optional[List[Card]]:
    """Check for four of a kind"""
    for rank in RANKS:
        same_rank = [card for card in cards if card.rank == rank]
        if len(same_rank) == 4:
            other_cards = [card for card in cards if card.rank != rank]
            return same_rank + [max(other_cards, key=lambda x: RANKS.index(x.rank))]
    return None

def check_full_house(cards: List[Card]) -> Optional[List[Card]]:
    """Check for full house"""
    three_kind = check_three_of_kind(cards)
    if three_kind:
        remaining = [card for card in cards if card.rank != three_kind[0].rank]
        pair = check_pair(remaining)
        if pair:
            return three_kind[:3] + pair[:2]
    return None

def check_flush(cards: List[Card]) -> Optional[List[Card]]:
    """Check for flush"""
    for suit in SUITS:
        suited_cards = [card for card in cards if card.suit == suit]
        if len(suited_cards) >= 5:
            return sorted(suited_cards, key=lambda x: RANKS.index(x.rank), reverse=True)[:5]
    return None

def check_straight(cards: List[Card]) -> Optional[List[Card]]:
    """Check for straight"""
    sorted_cards = sorted(cards, key=lambda x: RANKS.index(x.rank))
    for i in range(len(sorted_cards) - 4):
        potential_straight = sorted_cards[i:i+5]
        ranks = [RANKS.index(card.rank) for card in potential_straight]
        if ranks == list(range(min(ranks), max(ranks) + 1)):
            return potential_straight
    return None

def check_three_of_kind(cards: List[Card]) -> Optional[List[Card]]:
    """Check for three of a kind"""
    for rank in RANKS:
        same_rank = [card for card in cards if card.rank == rank]
        if len(same_rank) == 3:
            other_cards = sorted([card for card in cards if card.rank != rank],
                               key=lambda x: RANKS.index(x.rank), reverse=True)
            return same_rank + other_cards[:2]
    return None

def check_two_pair(cards: List[Card]) -> Optional[List[Card]]:
    """Check for two pair"""
    pairs = []
    for rank in RANKS:
        same_rank = [card for card in cards if card.rank == rank]
        if len(same_rank) == 2:
            pairs.append(same_rank)
    if len(pairs) >= 2:
        pairs = sorted(pairs, key=lambda x: RANKS.index(x[0].rank), reverse=True)[:2]
        other_cards = [card for card in cards if card.rank not in [p[0].rank for p in pairs]]
        return pairs[0] + pairs[1] + [max(other_cards, key=lambda x: RANKS.index(x.rank))]
    return None

def check_pair(cards: List[Card]) -> Optional[List[Card]]:
    """Check for pair"""
    for rank in RANKS:
        same_rank = [card for card in cards if card.rank == rank]
        if len(same_rank) == 2:
            other_cards = sorted([card for card in cards if card.rank != rank],
                               key=lambda x: RANKS.index(x.rank), reverse=True)
            return same_rank + other_cards[:3]
    return None

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from todos.models import Lobby, Player, GameRound
from django.urls import reverse

class GameFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.users = []
        for i in range(4):
            user = User.objects.create_user(
                username=f'testuser{i}',
                password='testpass123'
            )
            self.users.append(user)
            
        # Create test lobby
        self.lobby = Lobby.objects.create(
            name='test_lobby',
            creator=self.users[0],
            status='WAITING'
        )
        
        # Add players to lobby
        for i, user in enumerate(self.users):
            Player.objects.create(
                user=user,
                lobby=self.lobby,
                position=i,
                chips=1000
            )
    def test_create_lobby(self):
        """Test creating a new lobby"""
        client = APIClient()
        client.force_authenticate(user=self.users[0])
        
        response = client.post(reverse('create_lobby', args=['new_test_lobby']))
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Lobby.objects.filter(name='new_test_lobby').exists())

    def test_join_lobby(self):
        """Test joining an existing lobby"""
        client = APIClient()
        client.force_authenticate(user=self.users[1])
        
        response = client.post(reverse('join_lobby', args=[self.lobby.name]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Player.objects.filter(user=self.users[1], lobby=self.lobby).exists())

    def test_start_game(self):
        """Test starting a game"""
        client = APIClient()
        client.force_authenticate(user=self.users[0])
        
        response = client.post(reverse('start_game'))
        self.assertEqual(response.status_code, 200)
        
        self.lobby.refresh_from_db()
        self.assertEqual(self.lobby.status, 'IN_PROGRESS')
        
        # Check if cards were dealt
        for player in self.lobby.players.all():
            self.assertNotEqual(player.hole_cards, '')

    def test_betting_round(self):
        """Test betting actions during a game"""
        client = APIClient()
        self.lobby.status = 'IN_PROGRESS'
        self.lobby.save()
        
        GameRound.objects.create(
            lobby=self.lobby,
            round_number=1,
            current_stage='PREFLOP'
        )
        
        # Test call
        player = self.lobby.players.first()
        player.is_turn = True
        player.save()
        
        client.force_authenticate(user=player.user)
        response = client.post(reverse('call'))
        self.assertEqual(response.status_code, 200)
        
        # Test raise
        response = client.post(reverse('raise_bet'), {'amount': 50})
        self.assertEqual(response.status_code, 200)
        
        # Test fold
        response = client.post(reverse('fold'))
        self.assertEqual(response.status_code, 200)
        
        player.refresh_from_db()
        self.assertTrue(player.has_folded)

    def test_all_in_scenario(self):
        """Test all-in betting scenario"""
        client = APIClient()
        self.lobby.status = 'IN_PROGRESS'
        self.lobby.save()
        
        game_round = GameRound.objects.create(
            lobby=self.lobby,
            round_number=1
        )
        
        player = self.lobby.players.first()
        player.is_turn = True
        player.chips = 100  # Set low chips for all-in
        player.save()
        
        client.force_authenticate(user=player.user)
        response = client.post(reverse('raise_bet'), {'amount': 100})
        self.assertEqual(response.status_code, 200)
        
        player.refresh_from_db()
        game_round.refresh_from_db()
        
        self.assertEqual(player.chips, 0)
        self.assertIn(str(player.current_bet), game_round.side_pots)

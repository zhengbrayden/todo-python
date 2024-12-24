from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from todos.models import Lobby, Player, GameRound
from django.urls import reverse

class GameFlowTests(TestCase):
    def setUp(self):
        """Initialize test environment"""
        self.client = APIClient()
        
        # Create test users
        self.users = []
        for i in range(4):
            user = User.objects.create_user(
                username=f'testuser{i}',
                password='testpass123',
                email=f'testuser{i}@example.com'
            )
            self.users.append(user)
    def test_create_lobby(self):
        """Test creating a new lobby"""
        self.client.force_authenticate(user=self.users[0])
        
        response = self.client.post('/api/lobby/create/new_test_lobby/')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Lobby.objects.filter(name='new_test_lobby').exists())

    def test_join_lobby(self):
        """Test joining an existing lobby"""
        # Create a lobby first
        self.client.force_authenticate(user=self.users[0])
        self.client.post('/api/lobby/create/test_lobby/')
        
        # Switch to second user and try joining
        self.client.force_authenticate(user=self.users[1])
        response = self.client.post('/api/lobby/join/test_lobby/')
        self.assertEqual(response.status_code, 200)
        
        # Verify player was added
        self.assertTrue(
            Player.objects.filter(
                user=self.users[1],
                lobby__name='test_lobby'
            ).exists()
        )

    def test_start_game(self):
        """Test starting a game"""
        # Create and join lobby
        self.client.force_authenticate(user=self.users[0])
        self.client.post('/api/lobby/create/test_lobby/')
        
        self.client.force_authenticate(user=self.users[1])
        self.client.post('/api/lobby/join/test_lobby/')
        
        # Start game as lobby creator
        self.client.force_authenticate(user=self.users[0])
        response = self.client.post('/api/lobby/start/')
        self.assertEqual(response.status_code, 200)
        
        # Verify game started
        lobby = Lobby.objects.get(name='test_lobby')
        self.assertEqual(lobby.status, 'IN_PROGRESS')
        
        # Verify cards were dealt
        players = Player.objects.filter(lobby=lobby)
        for player in players:
            self.assertNotEqual(player.hole_cards, '')

    def test_betting_round(self):
        """Test betting actions during a game"""
        # Setup game
        self.client.force_authenticate(user=self.users[0])
        self.client.post('/api/lobby/create/test_lobby/')
        
        self.client.force_authenticate(user=self.users[1])
        self.client.post('/api/lobby/join/test_lobby/')
        
        self.client.force_authenticate(user=self.users[0])
        self.client.post('/api/lobby/start/')
        
        # Get active player
        lobby = Lobby.objects.get(name='test_lobby')
        player = Player.objects.get(lobby=lobby, is_turn=True)
        self.client.force_authenticate(user=player.user)
        
        # Test betting actions
        response = self.client.post('/api/lobby/call/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post('/api/lobby/raise/', {'amount': 50})
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post('/api/lobby/fold/')
        self.assertEqual(response.status_code, 200)
        
        # Verify fold
        player.refresh_from_db()
        self.assertTrue(player.has_folded)

    def test_all_in_scenario(self):
        """Test all-in betting scenario"""
        # Setup game
        self.client.force_authenticate(user=self.users[0])
        self.client.post('/api/lobby/create/test_lobby/')
        
        self.client.force_authenticate(user=self.users[1])
        self.client.post('/api/lobby/join/test_lobby/')
        
        self.client.force_authenticate(user=self.users[0])
        self.client.post('/api/lobby/start/')
        
        # Get active player and set up all-in scenario
        lobby = Lobby.objects.get(name='test_lobby')
        player = Player.objects.get(lobby=lobby, is_turn=True)
        player.chips = 100  # Set low chips for all-in
        player.save()
        
        # Perform all-in raise
        self.client.force_authenticate(user=player.user)
        response = self.client.post('/api/lobby/raise/', {'amount': 100})
        self.assertEqual(response.status_code, 200)
        
        # Verify all-in state
        player.refresh_from_db()
        self.assertEqual(player.chips, 0)
        
        # Verify side pot creation
        game_round = GameRound.objects.get(lobby=lobby)
        self.assertIn(str(player.current_bet), game_round.side_pots)

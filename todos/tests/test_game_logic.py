import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from ..models import Lobby, Player, GameRound
from django.urls import reverse

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_users():
    users = []
    for i in range(4):
        user = User.objects.create_user(
            username=f'testuser{i}',
            password='testpass123'
        )
        users.append(user)
    return users

@pytest.fixture
def test_lobby(test_users):
    lobby = Lobby.objects.create(
        name='test_lobby',
        creator=test_users[0],
        status='WAITING'
    )
    return lobby

@pytest.fixture
def game_with_players(test_lobby, test_users):
    for i, user in enumerate(test_users):
        Player.objects.create(
            user=user,
            lobby=test_lobby,
            position=i,
            chips=1000
        )
    return test_lobby

@pytest.mark.django_db
class TestGameFlow:
    def test_create_lobby(self, api_client, test_users):
        user = test_users[0]
        api_client.force_authenticate(user=user)
        
        response = api_client.post(reverse('create_lobby', args=['new_lobby']))
        assert response.status_code == 201
        assert Lobby.objects.filter(name='new_lobby').exists()

    def test_join_lobby(self, api_client, test_lobby, test_users):
        user = test_users[1]
        api_client.force_authenticate(user=user)
        
        response = api_client.post(reverse('join_lobby', args=[test_lobby.name]))
        assert response.status_code == 200
        assert Player.objects.filter(user=user, lobby=test_lobby).exists()

    def test_start_game(self, api_client, game_with_players, test_users):
        api_client.force_authenticate(user=test_users[0])
        
        response = api_client.post(reverse('start_game'))
        assert response.status_code == 200
        
        game_with_players.refresh_from_db()
        assert game_with_players.status == 'IN_PROGRESS'
        
        # Check if cards were dealt
        for player in game_with_players.players.all():
            assert player.hole_cards != ''

    def test_betting_round(self, api_client, game_with_players, test_users):
        # Start game
        game_with_players.status = 'IN_PROGRESS'
        game_with_players.save()
        
        GameRound.objects.create(
            lobby=game_with_players,
            round_number=1,
            current_stage='PREFLOP'
        )
        
        # Test call
        player = game_with_players.players.first()
        player.is_turn = True
        player.save()
        
        api_client.force_authenticate(user=player.user)
        response = api_client.post(reverse('call'))
        assert response.status_code == 200
        
        # Test raise
        response = api_client.post(reverse('raise_bet'), {'amount': 50})
        assert response.status_code == 200
        
        # Test fold
        response = api_client.post(reverse('fold'))
        assert response.status_code == 200
        
        player.refresh_from_db()
        assert player.has_folded

    def test_all_in_scenario(self, api_client, game_with_players, test_users):
        game_with_players.status = 'IN_PROGRESS'
        game_with_players.save()
        
        round = GameRound.objects.create(
            lobby=game_with_players,
            round_number=1
        )
        
        player = game_with_players.players.first()
        player.is_turn = True
        player.chips = 100  # Set low chips for all-in
        player.save()
        
        api_client.force_authenticate(user=player.user)
        response = api_client.post(reverse('raise_bet'), {'amount': 100})
        assert response.status_code == 200
        
        player.refresh_from_db()
        round.refresh_from_db()
        
        assert player.chips == 0
        assert str(player.current_bet) in round.side_pots

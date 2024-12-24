import random
from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Todo, Lobby, Player, GameRound
from .serializers import (
    TodoSerializer, UserSerializer, LobbySerializer,
    PlayerSerializer, GameRoundSerializer
)
from rest_framework.views import APIView
from .poker_utils import create_deck, deal_cards, serialize_cards

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            
            # Create username field from name field for django
            if 'name' in data:
                data['username'] = data.pop('name')
            
            serializer = self.get_serializer(data=data)
            if not serializer.is_valid():
                return Response(
                    {'error': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user already exists by username or email
            if User.objects.filter(username=data['username']).exists():
                return Response(
                    {'error': 'Username already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if User.objects.filter(email=data['email']).exists():
                return Response(
                    {'error': 'Email already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

#  • GET /todos/ - List todos (paginated)
#  • POST /todos/ - Create new todo
#  • GET /todos/{id}/ - Get specific todo
#  • PUT /todos/{id}/ - Update todo
#  • PATCH /todos/{id}/ - Partial update todo
#  • DELETE /todos/{id}/ - Delete todo

class HomeView(TemplateView):
    template_name = 'home.html'

class LobbyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lobby_name=None):
        # Determine which action to take based on the endpoint
        if self.request.path.startswith('/lobby/create/'):
            return self.create_lobby(request, lobby_name)
        elif self.request.path.startswith('/lobby/join/'):
            return self.join_lobby(request, lobby_name)
        elif self.request.path.startswith('/lobby/start/'):
            return self.start_game(request)
        elif self.request.path.startswith('/lobby/call/'):
            return self.call(request)
        elif self.request.path.startswith('/lobby/fold/'):
            return self.fold(request)
        elif self.request.path.startswith('/lobby/raise/'):
            return self.raise_bet(request)
        return Response({'error': 'Invalid endpoint'}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, lobby_name=None):
        # Handle GET requests for info endpoints
        if self.request.path.startswith('/lobby/info/'):
            if lobby_name:
                return self.get_lobby_info(request, lobby_name)
            return self.list_lobbies(request)
        elif self.request.path.startswith('/lobby/status/'):
            return self.get_player_status(request)
        return Response({'error': 'Invalid endpoint'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        # Handle leave lobby
        if self.request.path.startswith('/lobby/leave/'):
            return self.leave_lobby(request)
        return Response({'error': 'Invalid endpoint'}, status=status.HTTP_400_BAD_REQUEST)

    # Individual action methods
    def create_lobby(self, request, lobby_name):
        # Check if lobby already exists
        if Lobby.objects.filter(name=lobby_name).exists():
            return Response(
                {'error': 'Lobby already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new lobby
        lobby = Lobby.objects.create(
            name=lobby_name,
            creator=request.user,
            status='WAITING'
        )
        
        # Add creator as first player
        Player.objects.create(
            user=request.user,
            lobby=lobby,
            position=0
        )
        
        return Response(LobbySerializer(lobby).data, status=status.HTTP_201_CREATED)

    def join_lobby(self, request, lobby_name):
        try:
            lobby = Lobby.objects.get(name=lobby_name)
        except Lobby.DoesNotExist:
            return Response(
                {'error': 'Lobby not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if player is already in a lobby
        if Player.objects.filter(user=request.user, is_active=True).exists():
            return Response(
                {'error': 'Already in a lobby'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if lobby is full
        current_players = lobby.players.filter(is_active=True).count()
        if current_players >= lobby.max_players:
            return Response(
                {'error': 'Lobby is full'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if game already started
        if lobby.status != 'WAITING':
            return Response(
                {'error': 'Game already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Add player to lobby
        Player.objects.create(
            user=request.user,
            lobby=lobby,
            position=current_players
        )

        return Response(LobbySerializer(lobby).data)

    def leave_lobby(self, request):
        try:
            # Find player's active lobby
            player = Player.objects.get(user=request.user, is_active=True)
            lobby = player.lobby

            # Mark player as inactive
            player.is_active = False
            player.save()

            # If this was the creator and other players exist, transfer ownership
            if lobby.creator == request.user:
                next_player = lobby.players.filter(is_active=True).first()
                if next_player:
                    lobby.creator = next_player.user
                    lobby.save()

            # If no active players remain, mark lobby as finished
            if not lobby.players.filter(is_active=True).exists():
                lobby.status = 'FINISHED'
                lobby.save()

            return Response({'message': 'Successfully left lobby'})
        except Player.DoesNotExist:
            return Response(
                {'error': 'Not currently in any lobby'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def start_game(self, request):
        try:
            # Find player's active lobby
            player = Player.objects.get(user=request.user, is_active=True)
            lobby = player.lobby

            # Verify user is lobby creator
            if lobby.creator != request.user:
                return Response(
                    {'error': 'Only lobby creator can start the game'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check minimum players
            active_players = lobby.players.filter(is_active=True)
            if active_players.count() < lobby.min_players:
                return Response(
                    {'error': 'Not enough players to start'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Start the game
            lobby.status = 'IN_PROGRESS'
            lobby.save()

            # Initialize deck and deal cards
            deck = create_deck()
            random.shuffle(deck)
            
            # Create first game round
            game_round = GameRound.objects.create(
                lobby=lobby,
                round_number=1,
                dealer_position=0,
                deck=serialize_cards(deck)
            )
            
            # Deal hole cards to each player
            active_players = list(lobby.players.filter(is_active=True))
            for player in active_players:
                hole_cards = deal_cards(deck, 2)
                player.hole_cards = serialize_cards(hole_cards)
                player.save()
            
            # Update deck state
            game_round.deck = serialize_cards(deck)
            game_round.save()
            
            # Set up blinds
            small_blind_pos = (game_round.dealer_position + 1) % len(active_players)
            big_blind_pos = (game_round.dealer_position + 2) % len(active_players)
            
            # Post blinds
            small_blind_player = active_players[small_blind_pos]
            big_blind_player = active_players[big_blind_pos]
            
            small_blind_player.chips -= game_round.small_blind
            small_blind_player.current_bet = game_round.small_blind
            small_blind_player.save()
            
            big_blind_player.chips -= game_round.big_blind
            big_blind_player.current_bet = game_round.big_blind
            big_blind_player.save()
            
            # Set initial bet level
            lobby.current_bet = game_round.big_blind
            lobby.current_pot = game_round.small_blind + game_round.big_blind
            lobby.save()
            
            # Set first player's turn (after big blind)
            first_to_act = active_players[(big_blind_pos + 1) % len(active_players)]
            first_to_act.is_turn = True
            first_to_act.save()

            return Response({
                'message': 'Game started successfully',
                'lobby': LobbySerializer(lobby).data
            })
        except Player.DoesNotExist:
            return Response(
                {'error': 'Not currently in any lobby'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def list_lobbies(self, request):
        # Get all lobbies that are either waiting or in progress
        lobbies = Lobby.objects.filter(
            status__in=['WAITING', 'IN_PROGRESS']
        ).order_by('-created_at')
        
        return Response({
            'lobbies': LobbySerializer(lobbies, many=True).data
        })

    def get_lobby_info(self, request, lobby_name):
        try:
            lobby = Lobby.objects.get(name=lobby_name)
            return Response(LobbySerializer(lobby).data)
        except Lobby.DoesNotExist:
            return Response(
                {'error': 'Lobby not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def get_player_status(self, request):
        try:
            player = Player.objects.get(user=request.user, is_active=True)
            return Response({
                'player': PlayerSerializer(player).data,
                'lobby': LobbySerializer(player.lobby).data
            })
        except Player.DoesNotExist:
            return Response(
                {'error': 'Not currently in any lobby'},
                status=status.HTTP_404_NOT_FOUND
            )

    def call(self, request):
        try:
            player = Player.objects.get(user=request.user, is_active=True)
            lobby = player.lobby

            # Verify game is in progress
            if lobby.status != 'IN_PROGRESS':
                return Response(
                    {'error': 'Game is not in progress'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify it's player's turn
            if not player.is_turn:
                return Response(
                    {'error': 'Not your turn'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate call amount
            call_amount = lobby.current_bet - player.current_bet
            
            # Check if player has enough chips
            if player.chips < call_amount:
                return Response(
                    {'error': 'Not enough chips to call'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process the call
            player.chips -= call_amount
            player.current_bet = lobby.current_bet
            player.is_turn = False
            player.save()

            # Update lobby pot
            lobby.current_pot += call_amount
            lobby.save()

            # Check if we should advance game state
            self.advance_game_state(lobby)

            return Response({
                'message': 'Call successful',
                'amount': call_amount,
                'player': PlayerSerializer(player).data
            })
        except Player.DoesNotExist:
            return Response(
                {'error': 'Not currently in any lobby'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def fold(self, request):
        try:
            player = Player.objects.get(user=request.user, is_active=True)
            lobby = player.lobby

            # Verify game is in progress
            if lobby.status != 'IN_PROGRESS':
                return Response(
                    {'error': 'Game is not in progress'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify it's player's turn
            if not player.is_turn:
                return Response(
                    {'error': 'Not your turn'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process the fold
            player.has_folded = True
            player.is_turn = False
            player.save()

            # Check if only one player remains
            active_players = lobby.players.filter(
                is_active=True, 
                has_folded=False
            ).count()
            
            if active_players == 1:
                # End the round if only one player remains
                winner = lobby.players.get(is_active=True, has_folded=False)
                winner.chips += lobby.current_pot
                winner.save()
                
                # Start new round
                self.end_round(lobby)
            else:
                # Check if we should advance game state
                self.advance_game_state(lobby)

            return Response({
                'message': 'Fold successful',
                'player': PlayerSerializer(player).data
            })
        except Player.DoesNotExist:
            return Response(
                {'error': 'Not currently in any lobby'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def advance_game_state(self, lobby):
        """Helper method to advance game state after all players have acted"""
        current_round = lobby.rounds.last()
        active_players = lobby.players.filter(is_active=True, has_folded=False)
        deck = deserialize_cards(current_round.deck)
        
        # Check if all active players have acted (no one's turn)
        if not any(player.is_turn for player in active_players):
            if current_round.current_stage == 'PREFLOP':
                # Deal flop (3 cards)
                flop_cards = deal_cards(deck, 3)
                current_round.community_cards = serialize_cards(flop_cards)
                current_round.current_stage = 'FLOP'
            elif current_round.current_stage == 'FLOP':
                # Deal turn (1 card)
                turn_card = deal_cards(deck, 1)
                community_cards = deserialize_cards(current_round.community_cards)
                community_cards.extend(turn_card)
                current_round.community_cards = serialize_cards(community_cards)
                current_round.current_stage = 'TURN'
            elif current_round.current_stage == 'TURN':
                # Deal river (1 card)
                river_card = deal_cards(deck, 1)
                community_cards = deserialize_cards(current_round.community_cards)
                community_cards.extend(river_card)
                current_round.community_cards = serialize_cards(community_cards)
                current_round.current_stage = 'RIVER'
            elif current_round.current_stage == 'RIVER':
                self.showdown(lobby)
                return
            
            # Save updated deck and round state
            current_round.deck = serialize_cards(deck)
            current_round.save()
            
            # Reset betting for new stage
            lobby.current_bet = 0
            for player in active_players:
                player.current_bet = 0
                player.save()
            
            # Set next player's turn
            next_player = self.get_next_player(lobby)
            if next_player:
                next_player.is_turn = True
                next_player.save()

    def showdown(self, lobby):
        """Handle showdown and determine winner"""
        current_round = lobby.rounds.last()
        active_players = lobby.players.filter(is_active=True, has_folded=False)
        community_cards = deserialize_cards(current_round.community_cards)
        
        # Evaluate each player's hand
        player_hands = []
        for player in active_players:
            hole_cards = deserialize_cards(player.hole_cards)
            hand_name, best_cards = evaluate_hand(hole_cards, community_cards)
            player_hands.append({
                'player': player,
                'hand_name': hand_name,
                'best_cards': best_cards
            })
        
        # Sort hands by rank (using hand_name as proxy for now)
        # In a full implementation, would need more sophisticated comparison
        player_hands.sort(key=lambda x: [
            'High Card', 'Pair', 'Two Pair', 'Three of a Kind',
            'Straight', 'Flush', 'Full House', 'Four of a Kind',
            'Straight Flush'
        ].index(x['hand_name']), reverse=True)
        
        # Award pot to winner(s)
        winning_hand = player_hands[0]['hand_name']
        winners = [ph['player'] for ph in player_hands if ph['hand_name'] == winning_hand]
        
        # Split pot among winners
        split_amount = lobby.current_pot // len(winners)
        for winner in winners:
            winner.chips += split_amount
            winner.save()
        
        # Handle any remainder chips
        if lobby.current_pot % len(winners) > 0:
            winners[0].chips += lobby.current_pot % len(winners)
            winners[0].save()

        # Start new round
        self.start_new_round(lobby)

        # Reset player states
        for player in lobby.players.filter(is_active=True):
            player.has_folded = False
            player.current_bet = 0
            player.is_turn = False
            player.save()

        # Set first player's turn
        next_player = self.get_next_player(lobby)
        if next_player:
            next_player.is_turn = True
            next_player.save()

    def get_next_player(self, lobby):
        """Get the next player in turn order"""
        current_round = lobby.rounds.last()
        active_players = lobby.players.filter(
            is_active=True,
            has_folded=False
        ).order_by('position')
        
        if not active_players.exists():
            return None

        # Find current player
        current_player = active_players.filter(is_turn=True).first()
        
        if not current_player:
            # If no current player, start with player after dealer
            dealer_position = current_round.dealer_position
            next_players = active_players.filter(position__gt=dealer_position)
            if next_players.exists():
                return next_players.first()
            return active_players.first()
        
        # Find next player after current
        next_players = active_players.filter(position__gt=current_player.position)
        if next_players.exists():
            return next_players.first()
        return active_players.first()

    def start_new_round(self, lobby):
        """Initialize a new round of poker"""
        active_players = lobby.players.filter(is_active=True)
        current_round = lobby.rounds.last()
        
        # Reset game state
        lobby.current_pot = 0
        lobby.current_bet = 0
        lobby.save()
        
        # Create new deck and shuffle
        deck = create_deck()
        random.shuffle(deck)
        
        # Calculate new dealer position
        new_dealer_position = (current_round.dealer_position + 1) % active_players.count()
        
        # Create new round
        new_round = GameRound.objects.create(
            lobby=lobby,
            round_number=current_round.round_number + 1,
            dealer_position=new_dealer_position,
            deck=serialize_cards(deck)
        )
        
        # Deal new hole cards
        for player in active_players:
            hole_cards = deal_cards(deck, 2)
            player.hole_cards = serialize_cards(hole_cards)
            player.has_folded = False
            player.current_bet = 0
            player.is_turn = False
            player.save()
        
        # Update deck state
        new_round.deck = serialize_cards(deck)
        new_round.save()
        
        # Set first player's turn
        next_player = self.get_next_player(lobby)
        if next_player:
            next_player.is_turn = True
            next_player.save()

    def validate_bet(self, player, amount, action):
        """Validate if a betting action is legal"""
        lobby = player.lobby
        current_round = lobby.rounds.last()
        
        if not player.is_turn:
            return False, "Not your turn"
            
        if player.has_folded:
            return False, "Player has folded"
            
        if action == 'raise':
            # Minimum raise is double the current bet
            min_raise = lobby.current_bet * 2
            if amount < min_raise:
                return False, f"Minimum raise is {min_raise}"
                
            if amount > player.chips:
                return False, "Not enough chips"
                
        elif action == 'call':
            call_amount = lobby.current_bet - player.current_bet
            if call_amount > player.chips:
                return False, "Not enough chips to call"
                
        return True, None
        
    def raise_bet(self, request):
        amount = request.data.get('amount')
        if not amount:
            return Response(
                {'error': 'Amount required for raise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = int(amount)
        except ValueError:
            return Response(
                {'error': 'Amount must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            player = Player.objects.get(user=request.user, is_active=True)
            lobby = player.lobby

            # Verify game is in progress
            if lobby.status != 'IN_PROGRESS':
                return Response(
                    {'error': 'Game is not in progress'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify it's player's turn
            if not player.is_turn:
                return Response(
                    {'error': 'Not your turn'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Calculate total amount needed (call amount + raise amount)
            total_amount = (lobby.current_bet - player.current_bet) + amount

            # Check if player has enough chips
            if player.chips < total_amount:
                return Response(
                    {'error': 'Not enough chips for this raise'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process the raise
            player.chips -= total_amount
            player.current_bet += total_amount
            player.is_turn = False
            player.save()

            # Update lobby
            lobby.current_pot += total_amount
            lobby.current_bet = player.current_bet
            lobby.save()

            # Check if we should advance game state
            self.advance_game_state(lobby)

            return Response({
                'message': 'Raise successful',
                'amount': amount,
                'player': PlayerSerializer(player).data
            })
        except Player.DoesNotExist:
            return Response(
                {'error': 'Not currently in any lobby'},
                status=status.HTTP_400_BAD_REQUEST
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        try:
            # Handle both name/username and email login
            username = request.data.get('name')
            password = request.data.get('password')
            
            if not username or not password:
                return Response(
                    {'error': 'Username and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if login is via email or username
            if '@' in username:
                try:
                    user = User.objects.get(email=username)
                except User.DoesNotExist:
                    return Response(
                        {'error': 'User not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return Response(
                        {'error': 'User not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            # Authenticate user
            authenticated_user = authenticate(username=user.username, password=password)
            if authenticated_user:
                refresh = RefreshToken.for_user(authenticated_user)
                return Response({
                    'token': str(refresh.access_token),
                })
            else:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

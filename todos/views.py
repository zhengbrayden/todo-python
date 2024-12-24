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

            # Create first game round
            GameRound.objects.create(
                lobby=lobby,
                round_number=1,
                dealer_position=0
            )

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
                
                lobby.current_pot = 0
                lobby.current_bet = 0
                lobby.save()

            return Response({
                'message': 'Fold successful',
                'player': PlayerSerializer(player).data
            })
        except Player.DoesNotExist:
            return Response(
                {'error': 'Not currently in any lobby'},
                status=status.HTTP_400_BAD_REQUEST
            )

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

from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.generic import TemplateView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Todo
from .serializers import TodoSerializer, UserSerializer
from rest_framework.views import APIView
                                                                                                                                                                 
class TodoView(APIView):
    permission_classes = [IsAuthenticated]
                                                                                                                                                                
    # GET /todos/
    def get(self, request):
        todos = Todo.objects.filter(user=request.user)
        serializer = TodoSerializer(todos, many=True)
        return Response(serializer.data)
                                                                                                                                                                
    # POST /todos/
    def post(self, request):
        serializer = TodoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                                                                                                                                                                
# For individual todo operations
class TodoDetailView(APIView):
    permission_classes = [IsAuthenticated]
                                                                                                                                                                
    def get_object(self, pk, user):
        try:
            return Todo.objects.get(pk=pk, user=user)
        except Todo.DoesNotExist:
            return None
                                                                                                                                                                
    # GET /todos/<pk>/
    def get(self, request, pk):
        todo = self.get_object(pk, request.user)
        if not todo:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TodoSerializer(todo)
        return Response(serializer.data)
                                                                                                                                                                
    # PUT /todos/<pk>/
    def put(self, request, pk):
        todo = self.get_object(pk, request.user)
        if not todo:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TodoSerializer(todo, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                                                                                                                                                                
    # DELETE /todos/<pk>/
    def delete(self, request, pk):
        todo = self.get_object(pk, request.user)
        if not todo:
            return Response(status=status.HTTP_404_NOT_FOUND)
        todo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
                                                                                
class TodoView(APIView):
     permission_classes = [IsAuthenticated]
                                                                                                                                                                 
     # GET /todos/
     def get(self, request):
         todos = Todo.objects.filter(user=request.user)
         serializer = TodoSerializer(todos, many=True)
         return Response(serializer.data)
                                                                                                                                                                 
     # POST /todos/
     def post(self, request):
         serializer = TodoSerializer(data=request.data)
         if serializer.is_valid():
             serializer.save(user=request.user)
             return Response(serializer.data, status=status.HTTP_201_CREATED)
         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                                                                                                                                                                 
 # For individual todo operations
 class TodoDetailView(APIView):
     permission_classes = [IsAuthenticated]
                                                                                                                                                                 
     def get_object(self, pk, user):
         try:
             return Todo.objects.get(pk=pk, user=user)
         except Todo.DoesNotExist:
             return None
                                                                                                                                                                 
     # GET /todos/<pk>/
     def get(self, request, pk):
         todo = self.get_object(pk, request.user)
         if not todo:
             return Response(status=status.HTTP_404_NOT_FOUND)
         serializer = TodoSerializer(todo)
         return Response(serializer.data)
                                                                                                                                                                 
     # PUT /todos/<pk>/
     def put(self, request, pk):
         todo = self.get_object(pk, request.user)
         if not todo:
             return Response(status=status.HTTP_404_NOT_FOUND)
         serializer = TodoSerializer(todo, data=request.data)
         if serializer.is_valid():
             serializer.save()
             return Response(serializer.data)
         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                                                                                                                                                                 
     # DELETE /todos/<pk>/
     def delete(self, request, pk):
         todo = self.get_object(pk, request.user)
         if not todo:
             return Response(status=status.HTTP_404_NOT_FOUND)
         todo.delete()
         return Response(status=status.HTTP_204_NO_CONTENT)
                                                                                                                                                                 
                                                                                                                                                                 
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
class TodoViewSet(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Todo.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                'data': serializer.data,
                'page': int(request.query_params.get('page', 1)),
                'limit': int(request.query_params.get('limit', 10)),
                'total': self.get_queryset().count()
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
        elif self.request.path.startswith('/game/call/'):
            return self.call(request)
        elif self.request.path.startswith('/game/fold/'):
            return self.fold(request)
        elif self.request.path.startswith('/game/raise/'):
            return self.raise_bet(request)
        return Response({'error': 'Invalid endpoint'}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, lobby_name=None):
        # Handle GET requests for info endpoints
        if self.request.path.startswith('/lobby/info/'):
            if lobby_name:
                return self.get_lobby_info(request, lobby_name)
            return self.list_lobbies(request)
        elif self.request.path.startswith('/player/info/'):
            return self.get_player_info(request)
        return Response({'error': 'Invalid endpoint'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        # Handle leave lobby
        if self.request.path.startswith('/lobby/leave/'):
            return self.leave_lobby(request)
        return Response({'error': 'Invalid endpoint'}, status=status.HTTP_400_BAD_REQUEST)

    # Individual action methods
    def create_lobby(self, request, lobby_name):
        # TODO: Implement lobby creation logic
        return Response({'message': f'Created lobby: {lobby_name}'})

    def join_lobby(self, request, lobby_name):
        # TODO: Implement join lobby logic
        return Response({'message': f'Joined lobby: {lobby_name}'})

    def leave_lobby(self, request):
        # TODO: Implement leave lobby logic
        return Response({'message': 'Left lobby'})

    def start_game(self, request):
        # TODO: Implement start game logic
        return Response({'message': 'Game started'})

    def list_lobbies(self, request):
        # TODO: Implement list all lobbies logic
        return Response({'message': 'List of all lobbies'})

    def get_lobby_info(self, request, lobby_name):
        # TODO: Implement get specific lobby info logic
        return Response({'message': f'Info for lobby: {lobby_name}'})

    def get_player_info(self, request):
        # TODO: Implement get player info logic
        return Response({'message': 'Player info'})

    def call(self, request):
        # TODO: Implement call action logic
        return Response({'message': 'Called'})

    def fold(self, request):
        # TODO: Implement fold action logic
        return Response({'message': 'Folded'})

    def raise_bet(self, request):
        # Amount should be passed in request body
        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount required for raise'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        # TODO: Implement raise logic
        return Response({'message': f'Raised by {amount}'})


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

from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Todo
from .serializers import TodoSerializer, UserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            
            # Ensure either name or username is present
            if 'name' in data and 'username' not in data:
                data['username'] = data.pop('name')
            elif 'username' in data and 'name' not in data:
                data['name'] = data['username']
            
            serializer = self.get_serializer(data=data)
            if not serializer.is_valid():
                return Response(
                    {'error': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if user already exists
            if User.objects.filter(username=data['username']).exists():
                return Response(
                    {'error': 'User already exists'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'user': {
                    'username': user.username,
                    'email': user.email
                }
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

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
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        try:
            # Handle both name/username and email login
            username = request.data.get('name') or request.data.get('username')
            password = request.data.get('password')
            
            if not username or not password:
                return Response(
                    {'error': 'Username and password are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Try to get user by username first, then by email
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=username)
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
                    'user': {
                        'username': authenticated_user.username,
                        'email': authenticated_user.email
                    }
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

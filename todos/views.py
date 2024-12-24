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
                                                                                                                                                                 
 from rest_framework.views import APIView
 from rest_framework.response import Response
 from rest_framework import status
 from rest_framework.permissions import IsAuthenticated
                                                                                                                                                                 
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

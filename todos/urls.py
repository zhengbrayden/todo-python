from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView
from django.urls import path
from .views import CustomTokenObtainPairView
from .views import TodoViewSet, RegisterView, LobbyView

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    
    # Game lobby endpoints
    path('lobby/create/<str:lobby_name>/', LobbyView.as_view(), name='create_lobby'),
    path('lobby/join/<str:lobby_name>/', LobbyView.as_view(), name='join_lobby'),
    path('lobby/leave/', LobbyView.as_view(), name='leave_lobby'),
    path('lobby/start/', LobbyView.as_view(), name='start_game'),
    
    # Game info endpoints
    path('lobby/info/', LobbyView.as_view(), name='list_lobbies'),  # all lobbies
    path('lobby/info/<str:lobby_name>/', LobbyView.as_view(), name='lobby_info'),  # specific lobby
    path('player/info/', LobbyView.as_view(), name='player_info'),
    
    # Game action endpoints
    path('game/call/', LobbyView.as_view(), name='call'),
    path('game/fold/', LobbyView.as_view(), name='fold'),
    path('game/raise/', LobbyView.as_view(), name='raise_bet'),
]

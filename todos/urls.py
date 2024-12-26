from django.urls import path
from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import CustomTokenObtainPairView
from .views import RegisterView, LobbyView

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    
    # Lobby management
    path('lobby/create/<str:lobby_name>/', LobbyView.as_view(), name='create_lobby'),
    path('lobby/join/<str:lobby_name>/', LobbyView.as_view(), name='join_lobby'),
    path('lobby/leave/', LobbyView.as_view(), name='leave_lobby'),
    
    # Game state/info
    path('lobby/info/', LobbyView.as_view(), name='list_lobbies'),
    path('lobby/info/<str:lobby_name>/', LobbyView.as_view(), name='lobby_info'),
    path('lobby/status/', LobbyView.as_view(), name='player_status'),
    
    # Game actions
    path('lobby/start/', LobbyView.as_view(), name='start_game'),
    path('lobby/call/', LobbyView.as_view(), name='call'),
    path('lobby/fold/', LobbyView.as_view(), name='fold'),
    path('lobby/raise/', LobbyView.as_view(), name='raise_bet'),
]

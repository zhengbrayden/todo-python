from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView
from django.urls import path
from .views import CustomTokenObtainPairView
from .views import TodoViewSet, RegisterView, LobbyView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('lobby/', LobbyView.as_view()), #for create, join, 

# - `-call`: Call the current bet.
# - `-create <LOBBY>`: Create a new lobby with a unique name.
# - `-join <LOBBY>`: Join an existing lobby by name.
# - `-fold`: Fold your current hand.
# - `-info_lobby [LOBBY]`: Show all lobbies or players in a specific lobby.
# - `-info`: Get a DM with your player info for the current channel.
# - `-raise`: Raise the current bet.
# - `-leave`: Leave the current lobby.
# - `-start`: Start the game as the host.
]
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Todo, Lobby, Player, GameRound

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def create(self, data):
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        return user

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('id', 'title', 'description', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class PlayerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Player
        fields = ('username', 'chips', 'current_bet', 'is_active', 
                 'has_folded', 'is_turn', 'position')
        read_only_fields = ('chips', 'current_bet', 'is_active', 
                          'has_folded', 'is_turn', 'position')

class GameRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameRound
        fields = ('round_number', 'current_stage', 'dealer_position', 
                 'community_cards')
        read_only_fields = ('round_number', 'current_stage', 'dealer_position', 
                          'community_cards')

class LobbySerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True, read_only=True)
    current_round = serializers.SerializerMethodField()
    creator_name = serializers.CharField(source='creator.username', read_only=True)

    class Meta:
        model = Lobby
        fields = ('name', 'status', 'min_players', 'max_players', 
                 'current_pot', 'current_bet', 'creator_name', 
                 'players', 'current_round')
        read_only_fields = ('status', 'current_pot', 'current_bet', 
                          'creator_name', 'players', 'current_round')

    def get_current_round(self, obj):
        current_round = obj.rounds.last()
        if current_round:
            return GameRoundSerializer(current_round).data
        return None

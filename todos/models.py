from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Todo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Lobby(models.Model):
    GAME_STATUS_CHOICES = [
        ('WAITING', 'Waiting for players'),
        ('STARTING', 'Game starting'),
        ('IN_PROGRESS', 'Game in progress'),
        ('FINISHED', 'Game finished'),
    ]

    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=GAME_STATUS_CHOICES,
        default='WAITING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    min_players = models.IntegerField(default=2)
    max_players = models.IntegerField(default=6)
    current_pot = models.IntegerField(default=0)
    current_bet = models.IntegerField(default=0)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_lobbies'
    )

    def __str__(self):
        return f"{self.name} ({self.status})"

class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lobby = models.ForeignKey(
        Lobby,
        on_delete=models.CASCADE,
        related_name='players'
    )
    chips = models.IntegerField(default=1000)
    current_bet = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    has_folded = models.BooleanField(default=False)
    is_turn = models.BooleanField(default=False)
    position = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'lobby']

    def __str__(self):
        return f"{self.user.username} in {self.lobby.name}"

class GameRound(models.Model):
    ROUND_CHOICES = [
        ('PREFLOP', 'Pre-flop'),
        ('FLOP', 'Flop'),
        ('TURN', 'Turn'),
        ('RIVER', 'River'),
    ]

    lobby = models.ForeignKey(
        Lobby,
        on_delete=models.CASCADE,
        related_name='rounds'
    )
    round_number = models.IntegerField(default=1)
    current_stage = models.CharField(
        max_length=10,
        choices=ROUND_CHOICES,
        default='PREFLOP'
    )
    dealer_position = models.IntegerField(default=0)
    community_cards = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Round {self.round_number} in {self.lobby.name}"

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Todo

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

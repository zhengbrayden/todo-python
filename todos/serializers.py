from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Todo

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='username')
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('id', 'title', 'description', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

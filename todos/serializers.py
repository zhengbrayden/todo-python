from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Todo

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'username', 'email', 'password')

    def validate(self, data):
        # Ensure either name or username is provided
        if 'name' not in data and 'username' not in data:
            raise serializers.ValidationError(
                {"error": "Either name or username must be provided"}
            )
        
        # Map name to username if username is not provided
        if 'name' in data and 'username' not in data:
            data['username'] = data.pop('name')
        elif 'username' in data and 'name' not in data:
            data['name'] = data['username']
            
        return data

    def create(self, validated_data):
        name = validated_data.pop('name', None)  # Remove name as it's not needed for create_user
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

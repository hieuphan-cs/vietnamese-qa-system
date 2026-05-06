from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField() # Chỉ nhận vào chuỗi token

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role', 'avatar']
        read_only_fields = ['email']

class UserListDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'role', 'name', 'avatar', 
            'is_active', 'is_staff', 
            'created_at', 'updated_at'
        ]

class UserCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email', 'role', 'name', 'avatar', 
            'user_code', 'is_active', 'is_staff'
        ]
from rest_framework import serializers
from .models import CustomUser, UserRole
from django.db import IntegrityError


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'name', 'description']


class CustomUserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'role_display', 'department',
            'profile_picture', 'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']


class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'phone_number', 'role', 'department'
        ]
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        # Prevent duplicate username insertion by validating existence first
        username = validated_data.get('username')
        if username and CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'A user with that username already exists.'})

        user = CustomUser(**validated_data)
        user.set_password(password)
        try:
            user.save()
        except IntegrityError:
            # In case of a race condition leading to a DB-level unique constraint
            raise serializers.ValidationError({'username': 'A user with that username already exists.'})
        return user


class PublicUserRegistrationSerializer(serializers.ModelSerializer):
    """Inscription publique limitée au rôle citoyen."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'phone_number']

    def create(self, validated_data):
        password = validated_data.pop('password')
        username = validated_data.get('username')
        if username and CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'A user with that username already exists.'})

        user = CustomUser(role=UserRole.CITIZEN, **validated_data)
        user.set_password(password)
        try:
            user.save()
        except IntegrityError:
            raise serializers.ValidationError({'username': 'A user with that username already exists.'})
        return user

from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from rest_framework import serializers

from .models import CustomUser, UserRole
from .permissions import effective_role


ROLE_VALUES = dict(UserRole.ROLE_CHOICES)


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRole
        fields = ['id', 'name', 'description']


def _check_role_assignment(request, role):
    """Seuls les administrateurs peuvent attribuer le rôle administrateur."""
    if role == UserRole.ADMIN and effective_role(request.user) != UserRole.ADMIN:
        raise serializers.ValidationError(
            {'role': 'Seul un administrateur peut attribuer le rôle administrateur.'}
        )


class CustomUserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.SerializerMethodField()
    effective_role = serializers.SerializerMethodField()
    incident_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'role', 'role_display', 'effective_role', 'department',
            'profile_picture', 'is_active', 'is_superuser', 'date_joined',
            'last_login', 'incident_count',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_superuser']

    def get_full_name(self, user):
        return user.get_full_name() or user.username

    def get_effective_role(self, user):
        return effective_role(user)

    def validate_role(self, role):
        request = self.context.get('request')
        if request:
            _check_role_assignment(request, role)
        return role

    def validate(self, attrs):
        request = self.context.get('request')
        if request and self.instance:
            if self.instance.is_superuser and not request.user.is_superuser:
                raise serializers.ValidationError(
                    'Seul un super-administrateur peut modifier ce compte.'
                )
            if self.instance.pk == request.user.pk and attrs.get('is_active') is False:
                raise serializers.ValidationError(
                    {'is_active': 'Vous ne pouvez pas désactiver votre propre compte.'}
                )
        return attrs


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Création d'un compte par un gestionnaire (agents, décideurs, etc.)."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'phone_number', 'role', 'department',
        ]
        read_only_fields = ['id']

    def validate_role(self, role):
        request = self.context.get('request')
        if request:
            _check_role_assignment(request, role)
        return role

    def validate_password(self, password):
        validate_password(password)
        return password

    def create(self, validated_data):
        password = validated_data.pop('password')
        # Prevent duplicate username insertion by validating existence first
        username = validated_data.get('username')
        if username and CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'Ce nom d’utilisateur est déjà pris.'})

        user = CustomUser(**validated_data)
        user.set_password(password)
        try:
            user.save()
        except IntegrityError:
            # In case of a race condition leading to a DB-level unique constraint
            raise serializers.ValidationError({'username': 'Ce nom d’utilisateur est déjà pris.'})
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


class ProfileSerializer(serializers.ModelSerializer):
    """Champs qu'un utilisateur peut modifier sur son propre profil."""

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'department']


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Le mot de passe actuel est incorrect.')
        return value

    def validate_new_password(self, value):
        validate_password(value, self.context['request'].user)
        return value


class PasswordResetByManagerSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value, self.context.get('target_user'))
        return value

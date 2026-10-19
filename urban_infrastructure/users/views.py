from django.contrib.auth import authenticate
from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle

from .models import CustomUser, UserRole
from .permissions import IsManagerOrAdmin, effective_role
from .serializers import (
    CustomUserCreateSerializer,
    CustomUserSerializer,
    PasswordChangeSerializer,
    PasswordResetByManagerSerializer,
    ProfileSerializer,
    PublicUserRegistrationSerializer,
    UserRoleSerializer,
)


class LoginRateThrottle(SimpleRateThrottle):
    """Limite les tentatives de connexion par adresse IP (anti force brute)."""
    scope = 'login'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


def serialize_session_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name() or user.username,
        'role': user.role,
        'role_display': user.get_role_display(),
        'effective_role': effective_role(user),
        'is_superuser': user.is_superuser,
        'phone_number': user.phone_number,
        'department': user.department,
    }


def login_response(username, password):
    """Authentifie un utilisateur et produit la réponse token commune."""
    if not username or not password:
        return Response(
            {'detail': 'Username et password requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)
    if not user and '@' in username:
        # Permet aussi la connexion avec l'adresse e-mail.
        match = CustomUser.objects.filter(email__iexact=username).first()
        if match:
            user = authenticate(username=match.username, password=password)
    if not user:
        return Response(
            {'detail': 'Identifiants invalides'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': serialize_session_user(user)})


@api_view(['POST'])
@authentication_classes([])  # Pas de SessionAuthentication : évite le 403 CSRF si un cookie de session existe.
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    """Route publique et stable de connexion par token."""
    return login_response(request.data.get('username'), request.data.get('password'))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Révoque le token courant pour fermer réellement la session."""
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(viewsets.ModelViewSet):
    """Gestion des comptes : citoyens (usagers), agents, gestionnaires, décideurs."""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'department']
    ordering_fields = ['username', 'date_joined', 'last_login', 'role', 'incident_count']
    ordering = ['-date_joined']

    def get_queryset(self):
        queryset = CustomUser.objects.annotate(incident_count=Count('reported_incidents'))
        params = self.request.query_params
        role = params.get('role')
        if role in dict(UserRole.ROLE_CHOICES):
            queryset = queryset.filter(role=role)
        if params.get('is_active') in {'true', 'false'}:
            queryset = queryset.filter(is_active=params['is_active'] == 'true')
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            if has_management_access(self.request.user):
                return CustomUserCreateSerializer
            return PublicUserRegistrationSerializer
        return CustomUserSerializer

    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [AllowAny()]
        if self.action in [
            'list', 'retrieve', 'set_role', 'update', 'partial_update', 'destroy',
            'reset_password', 'toggle_active', 'stats',
        ]:
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if has_management_access(request.user):
            return Response(
                CustomUserSerializer(user, context=self.get_serializer_context()).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user.pk == request.user.pk:
            return Response(
                {'detail': 'Vous ne pouvez pas supprimer votre propre compte.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_superuser and not request.user.is_superuser:
            return Response(
                {'detail': 'Seul un super-administrateur peut supprimer ce compte.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Consulter ou mettre à jour le profil de l'utilisateur connecté."""
        if request.method == 'PATCH':
            serializer = ProfileSerializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        user = CustomUser.objects.annotate(
            incident_count=Count('reported_incidents'),
        ).get(pk=request.user.pk)
        return Response(CustomUserSerializer(user, context=self.get_serializer_context()).data)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        # Les autres sessions sont fermées ; un nouveau token est délivré.
        Token.objects.filter(user=request.user).delete()
        token = Token.objects.create(user=request.user)
        return Response({'token': token.key})

    @action(detail=True, methods=['post'])
    def set_role(self, request, pk=None):
        """Définir le rôle d'un utilisateur."""
        user = self.get_object()
        serializer = CustomUserSerializer(
            user,
            data={'role': request.data.get('role')},
            partial=True,
            context=self.get_serializer_context(),
        )
        if request.data.get('role') not in dict(UserRole.ROLE_CHOICES):
            return Response({'error': 'Role invalide'}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activer ou désactiver un compte sans perdre son historique."""
        user = self.get_object()
        serializer = CustomUserSerializer(
            user,
            data={'is_active': not user.is_active},
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if not user.is_active:
            Token.objects.filter(user=user).delete()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Définir un nouveau mot de passe provisoire pour un utilisateur."""
        user = self.get_object()
        if user.is_superuser and not request.user.is_superuser:
            return Response(
                {'detail': 'Seul un super-administrateur peut modifier ce compte.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = PasswordResetByManagerSerializer(
            data=request.data, context={'target_user': user},
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        Token.objects.filter(user=user).delete()
        return Response({'detail': 'Mot de passe réinitialisé.'})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Répartition des comptes par rôle et activité."""
        by_role = dict(
            CustomUser.objects.values_list('role').annotate(count=Count('id'))
        )
        return Response({
            'total': CustomUser.objects.count(),
            'active': CustomUser.objects.filter(is_active=True).count(),
            'inactive': CustomUser.objects.filter(is_active=False).count(),
            'citizens_with_reports': CustomUser.objects.filter(
                role=UserRole.CITIZEN,
            ).filter(~Q(reported_incidents=None)).distinct().count(),
            'by_role': [
                {'role': role, 'label': label, 'count': by_role.get(role, 0)}
                for role, label in UserRole.ROLE_CHOICES
            ],
        })

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], authentication_classes=[])
    def login(self, request):
        """Authentifier un utilisateur et retourner son token"""
        return login_response(request.data.get('username'), request.data.get('password'))


def has_management_access(user):
    return effective_role(user) in {'manager', 'admin'}


class UserRoleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les rôles utilisateur (lecture seule)"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]

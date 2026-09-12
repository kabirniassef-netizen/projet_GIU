from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import CustomUser, UserRole
from .serializers import (
    CustomUserSerializer, UserRoleSerializer, PublicUserRegistrationSerializer
)
from .permissions import IsManagerOrAdmin


def login_response(username, password):
    """Authentifie un utilisateur et produit la réponse token commune."""
    if not username or not password:
        return Response(
            {'detail': 'Username et password requis'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {'detail': 'Identifiants invalides'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'phone_number': user.phone_number
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Route publique et stable de connexion par token."""
    return login_response(request.data.get('username'), request.data.get('password'))


class CustomUserViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les utilisateurs"""
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PublicUserRegistrationSerializer
        return CustomUserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [AllowAny()]
        if self.action in ['list', 'retrieve', 'set_role', 'update', 'partial_update', 'destroy']:
            return [IsManagerOrAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Récupérer les informations de l'utilisateur connecté"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_role(self, request, pk=None):
        """Définir le rôle d'un utilisateur (admin only)"""
        user = self.get_object()
        role = request.data.get('role')
        
        if role not in dict(CustomUser.ROLE_CHOICES):
            return Response(
                {'error': 'Role invalide'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.role = role
        user.save()
        return Response(self.get_serializer(user).data)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Authentifier un utilisateur et retourner son token"""
        return login_response(request.data.get('username'), request.data.get('password'))


class UserRoleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les rôles utilisateur (lecture seule)"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated]

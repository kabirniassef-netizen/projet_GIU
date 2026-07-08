from django.db import models
from django.contrib.auth.models import AbstractUser


class UserRole(models.Model):
    """Rôles utilisateur disponibles"""
    CITIZEN = 'citizen'
    AGENT = 'agent'
    MANAGER = 'manager'
    DECISION_MAKER = 'decision_maker'
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (CITIZEN, 'Citoyen'),
        (AGENT, 'Agent Technique'),
        (MANAGER, 'Gestionnaire'),
        (DECISION_MAKER, 'Décideur'),
        (ADMIN, 'Administrateur'),
    ]
    
    name = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
    
    def __str__(self):
        return self.get_name_display()


class CustomUser(AbstractUser):
    """Modèle utilisateur personnalisé"""
    phone_number = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=50,
        choices=UserRole.ROLE_CHOICES,
        default=UserRole.CITIZEN
    )
    department = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

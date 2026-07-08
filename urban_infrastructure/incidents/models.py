from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class IncidentCategory(models.Model):
    """Catégories d'incidents"""
    LIGHTING = 'lighting'
    ROAD = 'road'
    WASTE = 'waste'
    SIGNAL = 'signal'
    WATER = 'water'
    TREE = 'tree'
    BENCH = 'bench'
    OTHER = 'other'
    
    CATEGORY_CHOICES = [
        (LIGHTING, 'Éclairage Public'),
        (ROAD, 'Voirie'),
        (WASTE, 'Déchets'),
        (SIGNAL, 'Signalisation'),
        (WATER, 'Eau'),
        (TREE, 'Arbres'),
        (BENCH, 'Mobilier Urbain'),
        (OTHER, 'Autre'),
    ]
    
    name = models.CharField(max_length=100, unique=True, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Incident Categories"
    
    def __str__(self):
        return self.get_name_display()


class Incident(models.Model):
    """Signalements d'incidents"""
    CREATED = 'created'
    VALIDATED = 'validated'
    IN_PROGRESS = 'in_progress'
    PLANNED = 'planned'
    RESOLVED = 'resolved'
    REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (CREATED, 'Créé'),
        (VALIDATED, 'Validé'),
        (PLANNED, 'Planifié'),
        (IN_PROGRESS, 'En cours'),
        (RESOLVED, 'Résolu'),
        (REJECTED, 'Rejeté'),
    ]
    
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'
    
    PRIORITY_CHOICES = [
        (LOW, 'Basse'),
        (MEDIUM, 'Moyenne'),
        (HIGH, 'Haute'),
        (URGENT, 'Urgente'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(IncidentCategory, on_delete=models.PROTECT, related_name='incidents')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_incidents')
    
    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.CharField(max_length=300, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=CREATED)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=MEDIUM)
    
    # Photo
    photo = models.ImageField(upload_to='incidents/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


class IncidentUpdate(models.Model):
    """Mises à jour du statut des incidents"""
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='updates')
    status = models.CharField(max_length=20, choices=Incident.STATUS_CHOICES)
    comment = models.TextField(blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.incident.title} - {self.get_status_display()}"

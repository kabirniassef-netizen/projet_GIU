import secrets

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

TRACKING_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def generate_tracking_code():
    """Code court et lisible remis au citoyen pour suivre son signalement."""
    return 'GIU-' + ''.join(secrets.choice(TRACKING_ALPHABET) for _ in range(8))


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
    IMPRUDENCE = 'imprudence'
    SPEEDING = 'vitesse'
    BREAKDOWN = 'panne'
    POOR_VISIBILITY = 'mauvaise_visibilite'
    ACCIDENT = 'accident'
    FLOOD = 'inondation'
    ENVIRONMENT = 'environnement'

    CATEGORY_CHOICES = [
        (LIGHTING, 'Lampadaire / Éclairage public'),
        (ROAD, 'Voirie'),
        (WASTE, 'Déchets'),
        (SIGNAL, 'Signalisation'),
        (WATER, 'Eau'),
        (TREE, 'Arbres'),
        (BENCH, 'Mobilier Urbain'),
        (OTHER, 'Autre'),
        (IMPRUDENCE, 'Imprudence'),
        (SPEEDING, 'Vitesse'),
        (BREAKDOWN, 'Panne'),
        (POOR_VISIBILITY, 'Mauvaise visibilité'),
        (ACCIDENT, 'Accident de la route'),
        (FLOOD, 'Inondation'),
        (ENVIRONMENT, 'Environnement'),
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

    ALLOWED_STATUS_TRANSITIONS = {
        CREATED: {VALIDATED, REJECTED},
        VALIDATED: {PLANNED, IN_PROGRESS, RESOLVED},
        PLANNED: {IN_PROGRESS, RESOLVED},
        IN_PROGRESS: {RESOLVED},
        RESOLVED: set(),
        REJECTED: set(),
    }
    # Retour automatique à « Validé » quand l'intervention liée est annulée,
    # afin de pouvoir replanifier l'incident.
    REOPEN_TRANSITIONS = {
        PLANNED: {VALIDATED},
        IN_PROGRESS: {VALIDATED},
    }
    
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
    reporter = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='reported_incidents',
        null=True,
        blank=True,
    )
    # Keep the precise road or landmark alongside the administrative location.
    region = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    commune = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=300, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=CREATED)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=MEDIUM)
    
    # Photo
    photo = models.ImageField(upload_to='incidents/', null=True, blank=True)

    # Code de suivi public communiqué au citoyen (y compris anonyme)
    tracking_code = models.CharField(
        max_length=12,
        unique=True,
        default=generate_tracking_code,
        editable=False,
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['priority']),
        ]

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_STATUS_TRANSITIONS.get(self.status, set())

    def allowed_next_statuses(self):
        return sorted(self.ALLOWED_STATUS_TRANSITIONS.get(self.status, set()))

    def reopen_for_planning(self):
        """Remet l'incident à « Validé » après l'annulation de son intervention."""
        self._reopening = True
        self.status = self.VALIDATED
        try:
            self.save()
        finally:
            self._reopening = False

    def save(self, *args, **kwargs):
        if self.pk:
            previous_status = type(self).objects.filter(pk=self.pk).values_list(
                'status', flat=True,
            ).first()
            if previous_status and previous_status != self.status:
                allowed = set(self.ALLOWED_STATUS_TRANSITIONS.get(previous_status, set()))
                if getattr(self, '_reopening', False):
                    allowed |= self.REOPEN_TRANSITIONS.get(previous_status, set())
                if self.status not in allowed:
                    raise ValidationError({'status': 'Transition de statut invalide.'})
        super().save(*args, **kwargs)
    
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

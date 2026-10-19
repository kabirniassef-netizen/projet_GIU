from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from urban_infrastructure.incidents.models import Incident

User = get_user_model()


class Intervention(models.Model):
    """Ordres de mission et interventions techniques"""
    PENDING = 'pending'
    ASSIGNED = 'assigned'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (PENDING, 'En Attente'),
        (ASSIGNED, 'Assignée'),
        (IN_PROGRESS, 'En Cours'),
        (COMPLETED, 'Complétée'),
        (CANCELLED, 'Annulée'),
    ]

    ACTIVE_STATUSES = (PENDING, ASSIGNED, IN_PROGRESS)

    ALLOWED_STATUS_TRANSITIONS = {
        PENDING: {ASSIGNED, IN_PROGRESS, CANCELLED},
        ASSIGNED: {IN_PROGRESS, CANCELLED},
        IN_PROGRESS: {COMPLETED, CANCELLED},
        COMPLETED: set(),
        CANCELLED: set(),
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
    
    # Un incident peut être replanifié après l'annulation d'une intervention.
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='interventions')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='interventions_assigned')
    
    # Planning
    scheduled_date = models.DateTimeField()
    estimated_duration = models.IntegerField(help_text='Durée estimée en minutes')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=MEDIUM)
    
    # Details
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-scheduled_date']

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_STATUS_TRANSITIONS.get(self.status, set())

    def save(self, *args, **kwargs):
        if self.pk:
            previous_status = type(self).objects.filter(pk=self.pk).values_list(
                'status', flat=True,
            ).first()
            if previous_status and previous_status != self.status:
                allowed = self.ALLOWED_STATUS_TRANSITIONS.get(previous_status, set())
                if self.status not in allowed:
                    raise ValidationError({'status': 'Transition de statut invalide.'})
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Intervention #{self.id} - {self.incident.title}"


class InterventionUpdate(models.Model):
    """Mises à jour du statut des interventions"""
    intervention = models.ForeignKey(Intervention, on_delete=models.CASCADE, related_name='updates')
    status = models.CharField(max_length=20, choices=Intervention.STATUS_CHOICES)
    comment = models.TextField(blank=True)
    photo = models.ImageField(upload_to='intervention_reports/', null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.intervention} - {self.get_status_display()}"

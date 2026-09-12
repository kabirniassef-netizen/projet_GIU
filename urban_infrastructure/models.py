from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. SECTION : ASSETS MANAGEMENT
# ==========================================

class AssetType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom du type")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Asset Type"
        verbose_name_plural = "Asset Types"


class Asset(models.Model):
    STATUS_CHOICES = [
        ('active', 'Opérationnel'),
        ('maintenance', 'En Maintenance'),
        ('broken', 'En Panne'),
        ('inactive', 'Inactif'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nom de l'équipement")
    serial_number = models.CharField(max_length=100, unique=True, verbose_name="Numéro de série")
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT, related_name="assets", verbose_name="Type d'équipement")
    location = models.CharField(max_length=250, verbose_name="Emplacement / Localisation")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="Statut")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'ajout")

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class AssetHistory(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="histories", verbose_name="Équipement")
    action = models.CharField(max_length=255, verbose_name="Action effectuée")
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Modifié par")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date de l'action")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes additionnelles")

    def __str__(self):
        return f"Historique de {self.asset.name} - {self.date.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Asset History"
        verbose_name_plural = "Asset Histories"


# ==========================================
# 2. SECTION : INCIDENTS MANAGEMENT
# ==========================================

class IncidentCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Incident Category"
        verbose_name_plural = "Incident Categories"


class Incident(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
        ('critical', 'Critique'),
    ]

    STATUS_CHOICES = [
        ('open', 'Ouvert'),
        ('in_progress', 'En cours de traitement'),
        ('resolved', 'Résolu'),
        ('closed', 'Clôturé'),
    ]

    title = models.CharField(max_length=200, verbose_name="Titre de l'incident")
    category = models.ForeignKey(IncidentCategory, on_delete=models.PROTECT, related_name="incidents", verbose_name="Catégorie")
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="incidents", verbose_name="Équipement concerné")
    description = models.TextField(verbose_name="Description du problème")
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='medium', verbose_name="Priorité")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', verbose_name="Statut")
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="reported_incidents", verbose_name="Signalé par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def __str__(self):
        return f"Inc #{self.id} - {self.title} ({self.get_status_display()})"


class IncidentUpdate(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="updates", verbose_name="Incident")
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Mis à jour par")
    comment = models.TextField(verbose_name="Commentaire / Avancement")
    new_status = models.CharField(max_length=20, choices=Incident.STATUS_CHOICES, blank=True, null=True, verbose_name="Nouveau statut (optionnel)")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date de mise à jour")

    def __str__(self):
        return f"Mise à jour pour Inc #{self.incident.id} le {self.date.strftime('%d/%m/%Y')}"

    class Meta:
        verbose_name = "Incident update"
        verbose_name_plural = "Incident updates"
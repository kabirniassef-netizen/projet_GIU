from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AssetType(models.Model):
    """Types d'actifs urbains"""
    LAMP_POST = 'lamp_post'
    TRAFFIC_LIGHT = 'traffic_light'
    SIGN = 'sign'
    BENCH = 'bench'
    BIN = 'bin'
    TREE = 'tree'
    WATER_VALVE = 'water_valve'
    MANHOLE = 'manhole'
    OTHER = 'other'
    
    TYPE_CHOICES = [
        (LAMP_POST, 'Candélabre/Lampadaire'),
        (TRAFFIC_LIGHT, 'Feu de Circulation'),
        (SIGN, 'Panneau de Signalisation'),
        (BENCH, 'Banc Public'),
        (BIN, 'Corbeille à Déchets'),
        (TREE, 'Arbre'),
        (WATER_VALVE, 'Vanne d\'Eau'),
        (MANHOLE, 'Chambre de Visite'),
        (OTHER, 'Autre'),
    ]
    
    name = models.CharField(max_length=100, unique=True, choices=TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Asset Types"
    
    def __str__(self):
        return self.get_name_display()


class Asset(models.Model):
    """Actifs urbains (équipements, mobiliers)"""
    OPERATIONAL = 'operational'
    UNDER_MAINTENANCE = 'under_maintenance'
    DEFECTIVE = 'defective'
    RETIRED = 'retired'
    
    STATUS_CHOICES = [
        (OPERATIONAL, 'Opérationnel'),
        (UNDER_MAINTENANCE, 'En Maintenance'),
        (DEFECTIVE, 'Défectueux'),
        (RETIRED, 'Retiré'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    asset_type = models.ForeignKey(AssetType, on_delete=models.PROTECT, related_name='assets')
    description = models.TextField(blank=True)
    
    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location = models.CharField(max_length=300)
    
    # Technical details
    model = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    specifications = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPERATIONAL)
    installed_date = models.DateField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class AssetHistory(models.Model):
    """Historique des actions sur les actifs"""
    REPAIR = 'repair'
    MAINTENANCE = 'maintenance'
    INSPECTION = 'inspection'
    STATUS_CHANGE = 'status_change'
    REPLACEMENT = 'replacement'
    OTHER = 'other'
    
    ACTION_CHOICES = [
        (REPAIR, 'Réparation'),
        (MAINTENANCE, 'Maintenance'),
        (INSPECTION, 'Inspection'),
        (STATUS_CHANGE, 'Changement de Statut'),
        (REPLACEMENT, 'Remplacement'),
        (OTHER, 'Autre'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Asset Histories"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.asset.code} - {self.get_action_display()}"

"""Calculs d'indicateurs partagés par le tableau de bord et les rapports."""
from datetime import timedelta

from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import TruncDate
from django.utils import timezone

from urban_infrastructure.assets.models import Asset
from urban_infrastructure.incidents.models import Incident, IncidentCategory, IncidentUpdate
from urban_infrastructure.interventions.models import Intervention


def _distribution(queryset, field, choices):
    counts = dict(queryset.values_list(field).annotate(count=Count('id')).order_by())
    return [
        {'key': key, 'label': label, 'count': counts.get(key, 0)}
        for key, label in choices
    ]


def average_resolution_hours(incidents):
    """Durée moyenne entre la création et la première résolution, en heures."""
    resolved_at = IncidentUpdate.objects.filter(
        incident=OuterRef('pk'),
        status=Incident.RESOLVED,
    ).order_by('updated_at').values('updated_at')[:1]
    durations = [
        (resolved - created).total_seconds()
        for created, resolved in incidents.filter(status=Incident.RESOLVED).annotate(
            resolved_at=Subquery(resolved_at),
        ).values_list('created_at', 'resolved_at')
        if resolved and created
    ]
    if not durations:
        return None
    return round(sum(durations) / len(durations) / 3600, 1)


def incident_summary(incidents, days=30):
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    total = incidents.count()
    resolved = incidents.filter(status=Incident.RESOLVED).count()
    daily = dict(
        incidents.filter(created_at__date__gte=start)
        .annotate(day=TruncDate('created_at'))
        .values_list('day')
        .annotate(count=Count('id'))
        .order_by()
    )
    categories = dict(
        IncidentCategory.objects.values_list('id', 'name')
    )
    category_labels = dict(IncidentCategory.CATEGORY_CHOICES)
    by_category = [
        {
            'key': categories.get(category_id),
            'label': category_labels.get(categories.get(category_id), categories.get(category_id)),
            'count': count,
        }
        for category_id, count in incidents.values_list('category').annotate(
            count=Count('id'),
        ).order_by('-count')
    ]
    return {
        'total': total,
        'resolved': resolved,
        'open': incidents.exclude(status__in=[Incident.RESOLVED, Incident.REJECTED]).count(),
        'awaiting_validation': incidents.filter(status=Incident.CREATED).count(),
        'awaiting_planning': incidents.filter(status=Incident.VALIDATED).count(),
        'urgent_open': incidents.filter(
            priority__in=[Incident.HIGH, Incident.URGENT],
        ).exclude(status__in=[Incident.RESOLVED, Incident.REJECTED]).count(),
        'resolution_rate': round(resolved / total * 100, 1) if total else 0,
        'avg_resolution_hours': average_resolution_hours(incidents),
        'last_30_days': incidents.filter(created_at__date__gte=start).count(),
        'by_status': _distribution(incidents, 'status', Incident.STATUS_CHOICES),
        'by_priority': _distribution(incidents, 'priority', Incident.PRIORITY_CHOICES),
        'by_category': by_category,
        'trend': [
            {
                'date': (start + timedelta(days=offset)).isoformat(),
                'count': daily.get(start + timedelta(days=offset), 0),
            }
            for offset in range(days)
        ],
    }


def intervention_summary(interventions):
    now = timezone.now()
    active = interventions.filter(status__in=Intervention.ACTIVE_STATUSES)
    return {
        'total': interventions.count(),
        'active': active.count(),
        'completed': interventions.filter(status=Intervention.COMPLETED).count(),
        'overdue': active.filter(scheduled_date__lt=now).count(),
        'next_7_days': active.filter(
            scheduled_date__gte=now,
            scheduled_date__lt=now + timedelta(days=7),
        ).count(),
        'by_status': _distribution(interventions, 'status', Intervention.STATUS_CHOICES),
    }


def asset_summary():
    total = Asset.objects.count()
    operational = Asset.objects.filter(status=Asset.OPERATIONAL).count()
    return {
        'total': total,
        'operational': operational,
        'availability_rate': round(operational / total * 100, 1) if total else 0,
        'by_status': _distribution(Asset.objects.all(), 'status', Asset.STATUS_CHOICES),
    }

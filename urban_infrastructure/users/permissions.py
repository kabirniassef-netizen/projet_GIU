from rest_framework.permissions import BasePermission


MANAGEMENT_ROLES = {'manager', 'admin'}
FIELD_ROLES = {'agent', 'manager', 'admin'}
REPORTING_ROLES = {'decision_maker', 'manager', 'admin'}


def effective_role(user):
    """Rôle applicatif réel : un superutilisateur agit toujours comme administrateur."""
    if not user or not user.is_authenticated:
        return None
    return 'admin' if user.is_superuser else user.role


def has_role(user, roles):
    return bool(user and user.is_authenticated and effective_role(user) in roles)


class IsManagerOrAdmin(BasePermission):
    """Autorise les gestionnaires, administrateurs et superutilisateurs."""
    def has_permission(self, request, view):
        return has_role(request.user, MANAGEMENT_ROLES)


class CanManageIncidents(BasePermission):
    """Les agents et la hiérarchie peuvent mettre à jour un incident."""
    def has_permission(self, request, view):
        return has_role(request.user, FIELD_ROLES)


class CanReportIncident(BasePermission):
    """Tout utilisateur connecté peut créer un signalement."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class CanUpdateInterventionStatus(BasePermission):
    """Les agents affectés et la hiérarchie peuvent suivre une intervention."""
    def has_permission(self, request, view):
        return has_role(request.user, FIELD_ROLES)


class CanConsultReports(BasePermission):
    """Les décideurs et la hiérarchie peuvent consulter les indicateurs."""
    def has_permission(self, request, view):
        return has_role(request.user, REPORTING_ROLES)

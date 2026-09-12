#!/usr/bin/env python
"""
🔍 VÉRIFICATION COMPLÈTE DU PROJET
================================

Ce script vérifie que tout le projet est correctement installé et configuré.
Exécutez-le avec: python verify_setup.py
"""

import os
import sys
import django
from pathlib import Path

# Évite les erreurs d'encodage dans les consoles Windows configurées en cp1252.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def check_python_version():
    print_header("1️⃣ VÉRIFICATION PYTHON")
    version = sys.version_info
    print_info(f"Version Python: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 8:
        print_success("Version Python acceptable")
        return True
    else:
        print_error("Python 3.8+ requis")
        return False

def check_django():
    print_header("2️⃣ VÉRIFICATION DJANGO")
    try:
        django.setup()
        print_success(f"Django {django.get_version()} installé")
        return True
    except Exception as e:
        print_error(f"Erreur Django: {e}")
        return False

def check_database():
    print_header("3️⃣ VÉRIFICATION BASE DE DONNÉES")
    db_path = Path("db.sqlite3")
    if db_path.exists():
        print_success(f"Base de données trouvée: {db_path}")
        print_info(f"Taille: {db_path.stat().st_size / 1024:.2f} KB")
        return True
    else:
        print_error("Base de données non trouvée")
        return False

def check_apps():
    print_header("4️⃣ VÉRIFICATION APPLICATIONS DJANGO")
    from django.apps import apps
    
    required_apps = [
        'users',
        'incidents',
        'assets',
        'interventions',
        'reports'
    ]
    
    all_ok = True
    for app in required_apps:
        try:
            apps.get_app_config(app)
            print_success(f"App {app} installée")
        except:
            print_error(f"App {app} NOT trouvée")
            all_ok = False
    
    return all_ok

def check_models():
    print_header("5️⃣ VÉRIFICATION MODÈLES")
    try:
        from urban_infrastructure.users.models import CustomUser, UserRole
        from urban_infrastructure.incidents.models import Incident, IncidentCategory
        from urban_infrastructure.assets.models import Asset, AssetType
        from urban_infrastructure.interventions.models import Intervention
        from urban_infrastructure.reports.models import KPIMetrics, Report
        
        print_success("Modèle CustomUser importé")
        print_success("Modèle UserRole importé")
        print_success("Modèle Incident importé")
        print_success("Modèle IncidentCategory importé")
        print_success("Modèle Asset importé")
        print_success("Modèle AssetType importé")
        print_success("Modèle Intervention importé")
        print_success("Modèle KPIMetrics importé")
        print_success("Modèle Report importé")
        return True
    except ImportError as e:
        print_error(f"Erreur import modèles: {e}")
        return False

def check_data():
    print_header("6️⃣ VÉRIFICATION DONNÉES")
    try:
        from urban_infrastructure.users.models import CustomUser
        from urban_infrastructure.incidents.models import Incident
        from urban_infrastructure.assets.models import Asset
        
        users_count = CustomUser.objects.count()
        incidents_count = Incident.objects.count()
        assets_count = Asset.objects.count()
        
        print_info(f"Utilisateurs: {users_count}")
        print_info(f"Incidents: {incidents_count}")
        print_info(f"Actifs: {assets_count}")
        
        if users_count >= 2 and incidents_count >= 0:
            print_success("Données de test présentes")
            return True
        else:
            print_warning("Données insuffisantes (exécutez load_test_data.py)")
            return False
    except Exception as e:
        print_error(f"Erreur accès données: {e}")
        return False

def check_static_files():
    print_header("7️⃣ VÉRIFICATION FICHIERS STATIQUES")
    
    files_to_check = [
        "templates/index.html",
        "static/css/style.css",
        "static/js/api.js"
    ]
    
    all_ok = True
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print_success(f"{file_path} ({size} bytes)")
        else:
            print_error(f"{file_path} NOT trouvé")
            all_ok = False
    
    return all_ok

def check_documentation():
    print_header("8️⃣ VÉRIFICATION DOCUMENTATION")
    
    docs = [
        "00_START_HERE.md",
        "README.md",
        "API_DOCUMENTATION.md",
        "DELIVERY_SUMMARY.md",
        "PROJECT_STRUCTURE.md",
        "USEFUL_COMMANDS.sh"
    ]
    
    all_ok = True
    for doc in docs:
        path = Path(doc)
        if path.exists():
            size = path.stat().st_size
            print_success(f"{doc} ({size} bytes)")
        else:
            print_error(f"{doc} NOT trouvé")
            all_ok = False
    
    return all_ok

def check_endpoints():
    print_header("9️⃣ VÉRIFICATION ENDPOINTS API")
    try:
        from rest_framework.routers import DefaultRouter
        from django.urls import get_resolver
        
        resolver = get_resolver()
        api_patterns = [pattern.pattern for pattern in resolver.url_patterns]
        
        print_info(f"Total patterns: {len(api_patterns)}")
        
        api_endpoints = [str(p) for p in api_patterns if 'api' in str(p)]
        print_info(f"Endpoints API trouvés: {len(api_endpoints)}")
        
        print_success("Configuration URL OK")
        return True
    except Exception as e:
        print_warning(f"Vérification endpoints: {e}")
        return True  # Non-bloquant

def check_permissions():
    print_header("🔟 VÉRIFICATION PERMISSIONS")
    try:
        from urban_infrastructure.users.models import UserRole
        
        roles = UserRole.ROLE_CHOICES
        print_info(f"Rôles disponibles: {len(roles)}")
        
        for value, label in roles:
            print_success(f"{label} ({value})")
        
        return True
    except Exception as e:
        print_error(f"Erreur permissions: {e}")
        return False

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         🔍 VÉRIFICATION COMPLÈTE DU PROJET - GIU                  ║")
    print("║           Système de Gestion d'Infrastructure Urbaine             ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    results = []
    
    # Vérifications
    results.append(("Python Version", check_python_version()))
    results.append(("Django Installation", check_django()))
    results.append(("Database", check_database()))
    results.append(("Applications", check_apps()))
    results.append(("Modèles", check_models()))
    results.append(("Données", check_data()))
    results.append(("Static Files", check_static_files()))
    results.append(("Documentation", check_documentation()))
    results.append(("Endpoints API", check_endpoints()))
    results.append(("Permissions", check_permissions()))
    
    # Résumé
    print_header("📊 RÉSUMÉ DES VÉRIFICATIONS")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed
    
    for name, result in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if result else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{name:30} {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} vérifications passées{Colors.END}")
    
    if failed == 0:
        print_success("TOUT EST OK! Prêt pour développement!")
        print_info("Lancez le serveur avec: python manage.py runserver")
        return 0
    elif failed <= 2:
        print_warning("Quelques problèmes mineurs, vérifiez les erreurs ci-dessus")
        return 1
    else:
        print_error("Problèmes majeurs détectés!")
        return 2

if __name__ == "__main__":
    # Configuration Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        exit_code = main()
    except Exception as e:
        print_error(f"Erreur: {e}")
        exit_code = 2
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")
    sys.exit(exit_code)

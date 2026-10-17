"""Point d'entrée de compatibilité vers le script de données de démonstration."""
import os
import sys
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from load_test_data import populate_test_data


if __name__ == '__main__':
    populate_test_data()

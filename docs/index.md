# CRES Validation

Outil de validation et correction de fichiers CSV pour le projet CRES.

## Fonctionnalités

- ✅ **Détection automatique** des lignes avec un nombre de colonnes incorrect
- ✅ **Correction automatique** des retours à la ligne intempestifs
- ✅ **Export des lignes rejetées** dans des fichiers CSV séparés
- ✅ **Support des gros fichiers** (millions de lignes) avec traitement optimisé
- ✅ **Logging configurable** avec niveaux de verbosité
- ✅ **Configuration flexible** via fichier INI
- ✅ **Tests unitaires** complets

## Démarrage rapide

```bash
# Installation
uv sync

# Validation
uv run python main.py

# Correction
uv run python main.py --correct -v
```

## Documentation

- [Installation](installation.md) - Guide d'installation
- [Configuration](configuration.md) - Configuration du projet
- [Utilisation](usage.md) - Guide d'utilisation
- [API](api.md) - Documentation de l'API
- [Tests](tests.md) - Guide des tests
- [Développement](development.md) - Guide pour les développeurs

## Exemple d'utilisation

```python
from cres_validation import csv_validate_columns_number, correct_csv
from pathlib import Path

# Valider un fichier CSV
csv_validate_columns_number(Path("data.csv"), delimiter=";")

# Corriger un fichier CSV
correct_csv(
    Path("data.csv"),
    Path("data_corrected.csv"),
    delimiter=";"
)
```

## Contribution

Les contributions sont les bienvenues ! Veuillez consulter le [guide de développement](development.md) pour plus d'informations.

## Licence

Ce projet est sous licence [AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html).

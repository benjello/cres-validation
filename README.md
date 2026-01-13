# Validation des données du CRES pour injection dans le Data Warehouse

[![CI](https://github.com/benjello/cres-validation/actions/workflows/ci.yml/badge.svg)](https://github.com/benjello/cres-validation/actions/workflows/ci.yml)

Outil de validation et correction de fichiers CSV pour le projet CRES.

## Fonctionnalités

- ✅ Détection des lignes avec un nombre de colonnes incorrect
- ✅ Correction automatique des retours à la ligne intempestifs
- ✅ Support des fichiers volumineux (millions de lignes)
- ✅ Logging configurable avec niveaux de verbosité
- ✅ Configuration via fichier INI

## Installation

```bash
# Cloner le repository
git clone https://github.com/benjello/cres-validation.git
cd cres-validation

# Installer les dépendances avec uv
uv sync
```

## Configuration

Le fichier de configuration est créé automatiquement au premier lancement dans `~/.config/cres-validation/config.ini`.

Vous pouvez aussi créer un fichier `config.ini` dans le répertoire du projet comme template.

## Utilisation

### Validation

```bash
# Valider les fichiers CSV
uv run python main.py

# Mode verbeux
uv run python main.py -v

# Mode très verbeux (debug)
uv run python main.py -vv
```

### Correction

```bash
# Corriger les fichiers CSV
uv run python main.py --correct

# Avec verbosité
uv run python main.py --correct -vv
```

## Tests

```bash
# Exécuter les tests
uv run pytest tests/ -v
```

## Structure du projet

```
cres-validation/
├── cres_validation/        # Package principal
│   ├── __init__.py        # Exports publics
│   ├── config.py          # Module de configuration
│   ├── config.ini         # Template de configuration
│   ├── columns_number_validator.py # Module de validation/correction CSV
│   ├── colums_validator.py # Schémas Pandera
│   ├── validate_columns.py # Validation avec Pandera
│   └── convert_txt_to_csv.py # Conversion TXT → CSV
├── main.py                # Point d'entrée principal
├── tests/                 # Tests unitaires
│   ├── fixtures/         # Fichiers de test
│   ├── test_columns_validator.py
│   └── test_convert_txt_to_csv.py
└── .github/workflows/     # CI/CD
    ├── ci.yml
    └── docs.yml
```

## Licence

Ce projet est sous licence [AGPL v3](LICENSE).

# Tests

Ce répertoire contient les tests unitaires pour le projet cres-validation.

## Structure

```
tests/
├── __init__.py
├── test_csv_validator.py    # Tests pour le module csv_validator
├── fixtures/                 # Fichiers de test
│   ├── input/
│   │   ├── source/          # Fichiers .txt originaux (avec espaces dans les noms)
│   │   └── csv/             # Fichiers .csv convertis (espaces remplacés par _)
│   ├── output/              # Répertoire pour les fichiers de sortie
│   │   └── expected_output.csv  # Fichier CSV attendu après correction
│   └── logs/                # Répertoire pour les logs
└── README.md                # Ce fichier
```

## Fichiers de test

- `fixtures/input/source/` : Répertoire contenant les fichiers .txt originaux (avec espaces dans les noms)
- `fixtures/input/csv/` : Répertoire contenant les fichiers .csv convertis (utilisés pour les tests)
- `fixtures/output/` : Répertoire pour les fichiers de sortie
  - `expected_output.csv` : Fichier CSV attendu après correction, avec toutes les lignes ayant le bon nombre de colonnes
- `fixtures/logs/` : Répertoire pour les logs générés par les tests

## Exécution des tests

```bash
# Exécuter tous les tests
uv run pytest

# Exécuter avec verbosité
uv run pytest -v

# Exécuter un test spécifique
uv run pytest tests/test_csv_validator.py::test_correct_csv

# Exécuter avec couverture
uv run pytest --cov=csv_validator tests/
```

## Tests disponibles

1. `test_input_file_exists` : Vérifie que le fichier d'entrée existe
2. `test_expected_output_file_exists` : Vérifie que le fichier de sortie attendu existe
3. `test_analyze_csv_columns` : Test de l'analyse des colonnes
4. `test_validate_csv` : Test de la validation du fichier CSV
5. `test_correct_csv` : Test de la correction du fichier CSV et comparaison avec le fichier attendu
6. `test_correct_csv_number_of_lines` : Test que la correction réduit le nombre de lignes

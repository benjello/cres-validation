# Tests

Ce répertoire contient les tests unitaires pour le projet cres-validation.

## Structure

```
tests/
├── __init__.py
├── test_csv_validator.py    # Tests pour le module csv_validator
├── fixtures/                 # Fichiers de test
│   ├── input.csv            # Fichier CSV d'entrée avec des problèmes
│   └── expected_output.csv  # Fichier CSV attendu après correction
└── README.md                # Ce fichier
```

## Fichiers de test

- `fixtures/input.csv` : Fichier CSV d'entrée contenant des lignes avec un nombre de colonnes incorrect (retours à la ligne intempestifs)
- `fixtures/expected_output.csv` : Fichier CSV attendu après correction, avec toutes les lignes ayant le bon nombre de colonnes (58)

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

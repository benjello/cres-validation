# Tests

## Exécution des tests

### Tous les tests

```bash
uv run pytest tests/ -v
```

### Test spécifique

```bash
uv run pytest tests/test_csv_validator.py::test_correct_csv -v
```

### Avec couverture

```bash
uv run pytest --cov=csv_validator tests/
```

## Structure des tests

Les tests sont organisés dans le répertoire `tests/` :

```
tests/
├── __init__.py
├── test_csv_validator.py    # Tests pour le module csv_validator
├── fixtures/                 # Fichiers de test
│   ├── input.csv            # Fichier CSV d'entrée avec des problèmes
│   └── expected_output.csv   # Fichier CSV attendu après correction
└── README.md
```

## Tests disponibles

### `test_input_file_exists`

Vérifie que le fichier d'entrée de test existe.

### `test_expected_output_file_exists`

Vérifie que le fichier de sortie attendu existe.

### `test_analyze_csv_columns`

Test de l'analyse des colonnes du fichier d'entrée :
- Vérifie que le nombre de colonnes attendu est détecté
- Vérifie qu'il y a des lignes problématiques
- Vérifie que le compteur contient des données

### `test_validate_csv`

Test de la validation du fichier CSV :
- Vérifie que la fonction ne lève pas d'exception
- Vérifie que les résultats sont cohérents

### `test_correct_csv`

Test de la correction du fichier CSV :
- Vérifie que le fichier corrigé est créé
- Compare avec le fichier attendu
- Vérifie que toutes les lignes ont le bon nombre de colonnes

### `test_correct_csv_number_of_lines`

Test que la correction réduit le nombre de lignes :
- Vérifie que le fichier corrigé a moins ou autant de lignes
- Vérifie que des lignes ont été fusionnées

## Fichiers de test

Les fichiers de test dans `tests/fixtures/` sont utilisés pour :

- **input.csv** : Fichier CSV d'entrée contenant des lignes avec un nombre de colonnes incorrect (retours à la ligne intempestifs)
- **expected_output.csv** : Fichier CSV attendu après correction, avec toutes les lignes ayant le bon nombre de colonnes (58)

Ces fichiers sont basés sur des données réelles du projet CRES.

## Ajouter de nouveaux tests

Pour ajouter un nouveau test :

1. Créer une fonction de test dans `tests/test_csv_validator.py`
2. Utiliser les fixtures existantes ou créer de nouvelles
3. Vérifier que le test passe : `uv run pytest tests/ -v`

## CI/CD

Les tests sont exécutés automatiquement sur GitHub Actions à chaque push ou pull request.

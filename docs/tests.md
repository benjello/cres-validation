# Tests

## Exécution des tests

### Tous les tests

```bash
uv run pytest tests/ -v
```

### Test spécifique

```bash
uv run pytest tests/test_columns_validator.py::test_correct_csv -v
```

### Avec couverture

```bash
uv run pytest --cov=cres_validation tests/
```

## Structure des tests

Les tests sont organisés dans le répertoire `tests/` :

```text
tests/
├── __init__.py
├── test_columns_validator.py # Tests pour le module columns_number_validator
├── test_convert_txt_to_csv.py # Tests pour la conversion TXT → CSV
├── test_performance.py        # Tests de performance
├── fixtures/                 # Fichiers de test
│   ├── input/               # Fichiers d'entrée
│   │   ├── source/          # Fichiers TXT source
│   │   └── csv/             # Fichiers CSV convertis
│   ├── output/              # Fichiers de sortie attendus
│   └── logs/                # Logs de test
└── README.md
```

## Tests disponibles

### Tests unitaires (`test_columns_validator.py`)

#### `test_input_file_exists`

Vérifie que le fichier d'entrée de test existe.

#### `test_expected_output_file_exists`

Vérifie que le fichier de sortie attendu existe.

#### `test_analyze_csv_columns`

Test de l'analyse des colonnes du fichier d'entrée :

- Vérifie que le nombre de colonnes attendu est détecté
- Vérifie que le header est traité séparément (peut avoir une colonne supplémentaire)
- Vérifie qu'il y a des lignes problématiques
- Vérifie que le compteur contient des données

#### `test_validate_csv`

Test de la validation du fichier CSV :

- Vérifie que la fonction ne lève pas d'exception
- Vérifie que les résultats sont cohérents

#### `test_correct_csv`

Test de la correction du fichier CSV :

- Vérifie que le fichier corrigé est créé
- Vérifie que le header est ajusté automatiquement (59 → 58 colonnes)
- Compare avec le fichier attendu
- Vérifie que toutes les lignes ont le bon nombre de colonnes

#### `test_correct_csv_reduces_line_count`

Test que la correction réduit le nombre de lignes :

- Vérifie que le fichier corrigé a moins ou autant de lignes
- Vérifie que des lignes ont été fusionnées

### Tests de conversion (`test_convert_txt_to_csv.py`)

Tests pour la conversion de fichiers TXT vers CSV, incluant la détection d'encodage et le remplacement des délimiteurs.

### Tests de performance (`test_performance.py`)


Tests pour mesurer les performances sur des fichiers de différentes tailles :

#### Tests rapides (1k lignes)
- `test_performance_convert_1k` : Conversion TXT → CSV
- `test_performance_analyze_1k` : Analyse des colonnes
- `test_performance_correct_1k` : Correction CSV

#### Tests lents (1M lignes) - marqués `@pytest.mark.slow`

- `test_performance_convert_1m` : Conversion TXT → CSV
- `test_performance_analyze_1m` : Analyse des colonnes
- `test_performance_correct_1m` : Correction CSV

**Note** : Les fichiers de test volumineux (1k et 1M lignes) sont générés à la volée à partir du fichier source, ils ne sont pas stockés dans le repository.

**Exécution** :

```bash
# Tests rapides uniquement
uv run pytest tests/test_performance.py -v

# Inclure les tests lents
uv run pytest tests/test_performance.py -v -m slow
```

## Fichiers de test

Les fichiers de test dans `tests/fixtures/` sont utilisés pour :

- **input/source/** : Fichiers TXT source avec des espaces dans les noms
- **input/csv/** : Fichiers CSV convertis depuis les fichiers TXT
- **output/** : Fichiers CSV attendus après correction (format: `corrected_{nom_source}.csv`)
- **logs/** : Logs générés lors des tests

### Format des logs de test

Les logs sont générés automatiquement lors des tests avec le format :

```text
nom_du_fichier-YYYY_MM_DD-HH_MM_SS.log
```

Exemple : `echantillon_cnrps_pb_fondation_fidaa-2026_01_13-13_37_25.log`

- Un seul log est produit par session de tests
- Le log capture tous les messages des modules de traitement
- Format avec date et heure lisibles (séparées par un tiret)

Ces fichiers sont basés sur des données réelles du projet CRES.

## Ajouter de nouveaux tests

Pour ajouter un nouveau test :

1. Créer une fonction de test dans `tests/test_columns_validator.py` (tests pour `columns_number_validator`)
2. Utiliser les fixtures existantes ou créer de nouvelles
3. Vérifier que le test passe : `uv run pytest tests/ -v`

## CI/CD

Les tests sont exécutés automatiquement sur GitHub Actions à chaque push ou pull request.

### Configuration CI

La CI est optimisée pour être rapide et fiable :

1. **Tests principaux** : Exclut les tests lents (`-m "not slow"`)
   - 20 tests rapides exécutés à chaque commit
   - CI plus rapide et fiable

2. **Tests de performance lents** : Job séparé avec `continue-on-error`
   - 3 tests lents (1M lignes) exécutés mais non bloquants
   - Permet de détecter les régressions de performance sans bloquer la CI

### Exécution locale

```bash
# Tous les tests (rapides uniquement)
uv run pytest tests/ -v

# Inclure les tests lents
uv run pytest tests/ -v -m slow

# Tests de performance uniquement
uv run pytest tests/test_performance.py -v
```

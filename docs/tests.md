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
├── test_convert_to_parquet.py # Tests de conformité CSV ↔ Parquet
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

#### `test_log_file_created_and_has_content`

Test de validation du fichier de log :

- Vérifie que le fichier de log est créé
- Vérifie que le fichier n'est pas vide
- Vérifie le format du nom du fichier (nom-date-heure.log)
- Vérifie que le fichier contient des messages formatés
- Vérifie que le fichier contient au moins un niveau de log (INFO, DEBUG, WARNING, ERROR)

### Tests de conversion (`test_convert_txt_to_csv.py`)

Tests pour la conversion de fichiers TXT vers CSV, incluant la détection d'encodage.

Le délimiteur est **fixé à `;`** (pas de conversion en `,`).

### Tests Parquet (`test_convert_to_parquet.py`)

Tests de conformité CSV ↔ Parquet :

- Vérifie que la conversion CSV → Parquet fonctionne
- Vérifie que les données dans le Parquet correspondent exactement au CSV (dimensions, colonnes, valeurs)

### Tests de performance (`test_performance.py`)

Tests pour mesurer les performances sur des fichiers de différentes tailles, incluant la mesure du temps d'exécution et de l'empreinte mémoire.

#### Tests rapides (1k lignes)

- `test_performance_convert_1k` : Conversion TXT → CSV
- `test_performance_analyze_1k` : Analyse des colonnes
- `test_performance_correct_1k` : Correction CSV

#### Tests lents (1M lignes) - marqués `@pytest.mark.slow`

- `test_performance_convert_1m` : Conversion TXT → CSV
- `test_performance_analyze_1m` : Analyse des colonnes avec mesure de RAM
- `test_performance_correct_1m` : Correction CSV avec mesure de RAM

**Fonctionnalités de mesure :**

- **Temps d'exécution** : Mesuré pour toutes les opérations
- **Empreinte mémoire (RAM)** : Mesurée pour les tests 1M lignes avec `psutil`
  - RAM utilisée (pic pendant l'opération)
  - RAM totale du processus
  - Vérification que la RAM reste < 2 GB pour 1M lignes

**Fonctions helper :**

Les tests utilisent des fonctions helper pour mutualiser le code :

- `prepare_test_csv()` : Prépare un fichier CSV de test (génération + conversion)
- `count_lines()` : Compte les lignes d'un fichier
- `format_time()` : Formate le temps en unité appropriée
- `format_memory()` : Formate la mémoire en unité appropriée
- `get_memory_usage()` : Mesure la mémoire résidente (RSS) du processus

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
- **output/csv/** : Fichiers CSV attendus après correction (format: `corrected_{nom_source}.csv`)
- **output/parquet/** : Versions Parquet des CSV corrigés (format: `corrected_{nom_source}.parquet`)
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
   - Mesure du temps d'exécution et de l'empreinte mémoire
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

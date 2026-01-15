# Utilisation

## Commandes de base

### Validation

Valider les fichiers TXT dans le répertoire d'entrée (conversion automatique en CSV) :

```bash
uv run python main.py
```

### Correction

Corriger les fichiers TXT en fusionnant les lignes incomplètes (conversion automatique en CSV) :

```bash
uv run python main.py --correct
```

## Options de verbosité

Contrôler le niveau de détail des messages :

```bash
# Mode silencieux (WARNING et ERROR uniquement)
uv run python main.py

# Mode verbeux (INFO, WARNING, ERROR)
uv run python main.py -v
# ou
uv run python main.py --verbose

# Mode très verbeux (DEBUG, INFO, WARNING, ERROR)
uv run python main.py -vv
```

## Exemples d'utilisation

### Validation simple

```bash
uv run python main.py
```

Sortie :

```text
INFO - 1 fichier(s) TXT trouvé(s)
INFO - Conversion: data.txt → data.csv
INFO - 1 fichier(s) TXT converti(s) en CSV
INFO - Analyse du fichier: data.csv
INFO - Nombre de colonnes attendu: 58
WARNING - 5 ligne(s) avec un nombre de colonnes incorrect
```

### Correction avec verbosité

```bash
uv run python main.py --correct -vv
```

Sortie détaillée avec tous les messages de debug.

### Utilisation programmatique

```python
from pathlib import Path
from cres_validation import csv_validate_columns_number, correct_csv

# Valider un fichier
from cres_validation.config import get_delimiter

delimiter = get_delimiter()  # Récupère depuis CRES_CSV_DELIMITER ou ';' par défaut
csv_validate_columns_number(
    Path("data.csv"),
    delimiter=delimiter,
    show_progress=True
)

# Corriger un fichier
correct_csv(
    Path("data.csv"),
    Path("data_corrected.csv"),
    delimiter=delimiter,
    show_progress=True
)
```

## Fichiers de log

Les fichiers de log sont créés automatiquement dans le répertoire `log_dir` configuré, avec le format :

```text
cres-validation-{mode}-{date-iso}.log
```

Exemple : `cres-validation-correction-2026-01-12.log`

**Format des logs de test** :

Les tests génèrent également des logs dans `tests/fixtures/logs/` avec le format :

```text
nom_du_fichier-YYYY_MM_DD-HH_MM_SS.log
```

Exemple : `echantillon_cnrps_pb_fondation_fidaa-2026_01_13-13_37_25.log`

- Date et heure lisibles, séparées par un tiret
- Un seul log produit par session de tests
- Capture tous les messages des modules de traitement

Tous les messages (tous niveaux) sont écrits dans le fichier de log, même si la console n'affiche que certains niveaux.

## Traitement de plusieurs fichiers

Le script traite automatiquement tous les fichiers `.txt` dans le répertoire `source_dir`. Les fichiers TXT sont automatiquement convertis en CSV avant validation/correction :

```text
source_dir/
├── fichier1.txt
├── fichier2.txt
└── fichier3.txt
```

Chaque fichier TXT sera :

1. Converti automatiquement en CSV (le délimiteur `;` est conservé)
2. Validé ou corrigé selon le mode choisi
3. Les fichiers CSV temporaires sont nettoyés automatiquement

## Résultats de la correction

Après correction, vous obtiendrez :

- **Fichiers corrigés (CSV)** dans `output_dir/csv/` avec le format `corrected_{nom_source}.csv`
- **Fichiers corrigés (Parquet)** dans `output_dir/parquet/` avec le format `corrected_{nom_source}.parquet`
- **Fichiers de lignes rejetées** dans `output_dir/rejected/` avec le format `rejected_{nom_source}.csv`
- **Header ajusté automatiquement** : si le header a une colonne supplémentaire, elle est supprimée
- **Fichiers de log** dans `log_dir` avec les détails de l'opération
- **Statistiques** : nombre de lignes originales, lignes corrigées, lignes finales

### Fichiers de lignes rejetées

Les lignes problématiques (avec un nombre de colonnes incorrect ou des dates invalides) sont sauvegardées dans des fichiers CSV séparés dans le répertoire `output_dir/rejected/`. Ces fichiers contiennent :

- Les lignes avec un nombre de colonnes incorrect (qui seront fusionnées lors de la correction)
- Les lignes avec des dates invalides (détectées lors de la validation Pandera)
- Le header du fichier original pour faciliter l'analyse

Chaque ligne problématique est conservée avec sa ligne suivante (si applicable) pour permettre de comprendre le contexte de la fusion.

### Ajustement automatique du header

Le système détecte automatiquement si le header a une colonne supplémentaire par rapport aux données (ex: 59 vs 58 colonnes) et ajuste le header en conséquence. Le header corrigé aura le même nombre de colonnes que les lignes de données.

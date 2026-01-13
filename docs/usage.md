# Utilisation

## Commandes de base

### Validation

Valider les fichiers CSV dans le répertoire d'entrée :

```bash
uv run python main.py
```

### Correction

Corriger les fichiers CSV en fusionnant les lignes incomplètes :

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
```
INFO - 1 fichier(s) CSV trouvé(s)
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
from cres_validation import validate_csv, correct_csv

# Valider un fichier
validate_csv(
    Path("data.csv"),
    delimiter=",",
    show_progress=True
)

# Corriger un fichier
correct_csv(
    Path("data.csv"),
    Path("data_corrected.csv"),
    delimiter=",",
    show_progress=True
)
```

## Fichiers de log

Les fichiers de log sont créés automatiquement dans le répertoire `log_dir` configuré, avec le format :

```
cres-validation-{mode}-{date-iso}.log
```

Exemple : `cres-validation-correction-2026-01-12.log`

Tous les messages (tous niveaux) sont écrits dans le fichier de log, même si la console n'affiche que certains niveaux.

## Traitement de plusieurs fichiers

Le script traite automatiquement tous les fichiers `.csv` dans le répertoire `input_dir` :

```
input_dir/
├── fichier1.csv
├── fichier2.csv
└── fichier3.csv
```

Chaque fichier sera validé ou corrigé selon le mode choisi.

## Résultats de la correction

Après correction, vous obtiendrez :

- **Fichiers corrigés** dans `output_dir` avec le même nom que les originaux
- **Fichiers de log** dans `log_dir` avec les détails de l'opération
- **Statistiques** : nombre de lignes originales, lignes corrigées, lignes finales

# Référence API

## Package `cres_validation`

Le package `cres_validation` contient tous les modules nécessaires pour la validation et la correction de fichiers CSV.

### Imports recommandés

```python
# Import depuis le package
from cres_validation import validate_csv, correct_csv, get_config

# Ou import depuis les modules spécifiques
from cres_validation.columns_number_validator import analyze_csv_columns
from cres_validation.config import get_config
```

## Module `cres_validation.columns_number_validator`

Ce module contient les fonctions pour valider et corriger le nombre de colonnes dans les fichiers CSV. Il détecte les lignes avec un nombre de colonnes incorrect (généralement causé par des retours à la ligne intempestifs) et peut les corriger automatiquement.

### `analyze_csv_columns()`

Analyse un fichier CSV pour détecter les lignes avec un nombre de colonnes incorrect.

**Fonctionnalités importantes :**

- Le header est traité séparément des lignes de données
- Le header peut avoir une colonne supplémentaire (ex: 59 vs 58 colonnes)
- Le nombre de colonnes attendu est basé uniquement sur les lignes de données
- Optimisé pour les gros fichiers (millions de lignes) avec traitement en deux passes

```python
def analyze_csv_columns(
    csv_path: Path,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    use_most_frequent: bool = True,
    show_progress: bool = True,
    chunk_size: int = 100000,
    logger: Optional[logging.Logger] = None
) -> Tuple[int, List[int], Counter, dict]
```

**Paramètres :**

- `csv_path` : Chemin vers le fichier CSV
- `delimiter` : Délimiteur utilisé (défaut: `,`)
- `encoding` : Encodage du fichier (défaut: `utf-8`)
- `use_most_frequent` : Utiliser le nombre de colonnes le plus fréquent (défaut: `True`)
- `show_progress` : Afficher la progression (défaut: `True`)
- `chunk_size` : Taille des chunks pour la progression (défaut: `100000`)
- `logger` : Logger optionnel

**Retourne :**

- `expected_columns` : Nombre de colonnes attendu (basé sur les lignes de données, pas le header)
- `problematic_lines_list` : Liste des numéros de lignes problématiques
- `column_counter` : Counter avec la répartition des colonnes (lignes de données uniquement)
- `problematic_lines_dict` : Dictionnaire {line_num: col_count} des lignes problématiques

**Exemple :**

```python
from pathlib import Path
from cres_validation.columns_number_validator import analyze_csv_columns

expected, problematic, counter, details = analyze_csv_columns(
    Path("data.csv"),
    delimiter=","
)
print(f"Colonnes attendues: {expected}")
print(f"Lignes problématiques: {len(problematic)}")
```

### `validate_csv()`

Valide un fichier CSV et affiche les lignes problématiques.

```python
def validate_csv(
    csv_path: Path,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    show_progress: bool = True,
    max_problematic_display: int = 100,
    logger: Optional[logging.Logger] = None
) -> None
```

**Paramètres :**

- `csv_path` : Chemin vers le fichier CSV
- `delimiter` : Délimiteur utilisé
- `encoding` : Encodage du fichier
- `show_progress` : Afficher la progression
- `max_problematic_display` : Nombre maximum de lignes problématiques à afficher
- `logger` : Logger optionnel

**Exemple :**

```python
from pathlib import Path
from cres_validation import validate_csv

validate_csv(Path("data.csv"), delimiter=",")
```

### `correct_csv()`

Corrige un fichier CSV en fusionnant les lignes incomplètes.

**Fonctionnalités importantes :**

- Ajuste automatiquement le header si nécessaire (supprime les colonnes vides en trop)
- Compare le header avec la première ligne de données pour détecter les colonnes supplémentaires
- Fusionne les lignes incomplètes avec les lignes suivantes jusqu'à obtenir le bon nombre de colonnes
- Optimisé pour les gros fichiers avec traitement en deux passes

```python
def correct_csv(
    csv_path: Path,
    output_path: Path,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    show_progress: bool = True,
    chunk_size: int = 100000,
    logger: Optional[logging.Logger] = None
) -> None
```

**Paramètres :**

- `csv_path` : Chemin vers le fichier CSV à corriger
- `output_path` : Chemin vers le fichier CSV corrigé
- `delimiter` : Délimiteur utilisé
- `encoding` : Encodage du fichier
- `show_progress` : Afficher la progression
- `chunk_size` : Taille des chunks pour la progression
- `logger` : Logger optionnel

**Comportement :**

- Si le header a une colonne de plus que les données, la dernière colonne vide est supprimée
- Le header ajusté est écrit avec le même nombre de colonnes que les données
- Les lignes de données sont fusionnées si elles ont moins de colonnes que le nombre attendu

**Exemple :**

```python
from pathlib import Path
from cres_validation import correct_csv

correct_csv(
    Path("data.csv"),
    Path("data_corrected.csv"),
    delimiter=","
)
```

## Module `cres_validation.config`

### `ConfigReader`

Classe pour lire la configuration depuis un fichier INI.

```python
class ConfigReader:
    def __init__(self, config_path: Optional[Path] = None)
    def get_path(self, section: str, key: str) -> Path
    def get_paths(self, section: str) -> dict[str, Path]
    def get(self, section: str, key: str, fallback: Optional[str] = None) -> str
    def reload(self) -> None
```

**Méthodes :**

- `get_path(section, key)` : Récupère un chemin de fichier
- `get_paths(section)` : Récupère tous les chemins d'une section
- `get(section, key, fallback)` : Récupère une valeur de configuration
- `reload()` : Recharge le fichier de configuration

**Exemple :**

```python
from cres_validation import get_config

config = get_config()
input_dir = config.get_path("paths", "input_dir")
delimiter = config.get("csv", "delimiter", fallback=",")
```

### `get_config()`

Obtient l'instance globale du lecteur de configuration.

```python
def get_config(config_path: Optional[Path] = None) -> ConfigReader
```

## Module `cres_validation.validate_columns`

### `validate_csv_columns()`

Valide les colonnes d'un CSV avec les schémas Pandera.

**Note** : Ce module utilise l'API recommandée de Pandera (`pandera.pandas`) pour éviter les warnings de dépréciation.

```python
def validate_csv_columns(
    csv_path: Path,
    delimiter: str = ',',
    table_name: str = 'individu',
    column_mapping: dict | None = None
) -> bool
```

**Exemple :**

```python
from pathlib import Path
from cres_validation import validate_csv_columns

success = validate_csv_columns(
    Path("data.csv"),
    delimiter=",",
    table_name="individu"
)
```

## Module `cres_validation.colums_validator`

Ce module définit les schémas Pandera pour la validation des colonnes.

**Note** : Utilise `import pandera.pandas as pa` pour l'API recommandée de Pandera.

### Schémas disponibles

- `schema_by_table["individu"]` : Schéma pour la table individu
- `schema_by_table["menage"]` : Schéma pour la table ménage

## Module `cres_validation.convert_txt_to_csv`

### `convert_txt_to_csv()`

Convertit les fichiers `.txt` en `.csv` en remplaçant les délimiteurs.

```python
def convert_txt_to_csv(source_dir: Path, csv_dir: Path) -> None
```

**Exemple :**

```python
from pathlib import Path
from cres_validation import convert_txt_to_csv

convert_txt_to_csv(
    Path("input/source"),
    Path("input/csv")
)
```

### `detect_encoding()`

Détecte l'encodage d'un fichier texte.

```python
def detect_encoding(file_path: Path) -> str
```

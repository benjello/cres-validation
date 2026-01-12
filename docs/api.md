# API Reference

## Module `csv_validator`

### `analyze_csv_columns()`

Analyse un fichier CSV pour détecter les lignes avec un nombre de colonnes incorrect.

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

- `expected_columns` : Nombre de colonnes attendu
- `problematic_lines_list` : Liste des numéros de lignes problématiques
- `column_counter` : Counter avec la répartition des colonnes
- `problematic_lines_dict` : Dictionnaire {line_num: col_count} des lignes problématiques

**Exemple :**

```python
from pathlib import Path
from csv_validator import analyze_csv_columns

expected, problematic, counter, details = analyze_csv_columns(
    Path("data.csv"),
    delimiter=";"
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
from csv_validator import validate_csv

validate_csv(Path("data.csv"), delimiter=";")
```

### `correct_csv()`

Corrige un fichier CSV en fusionnant les lignes incomplètes.

```python
def correct_csv(
    csv_path: Path,
    output_path: Path,
    delimiter: str = ';',
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

**Exemple :**

```python
from pathlib import Path
from csv_validator import correct_csv

correct_csv(
    Path("data.csv"),
    Path("data_corrected.csv"),
    delimiter=";"
)
```

## Module `config`

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
from config import get_config

config = get_config()
input_dir = config.get_path("paths", "input_dir")
delimiter = config.get("csv", "delimiter", fallback=";")
```

### `get_config()`

Obtient l'instance globale du lecteur de configuration.

```python
def get_config(config_path: Optional[Path] = None) -> ConfigReader
```

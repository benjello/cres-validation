# Configuration

Le projet utilise un fichier de configuration INI pour gérer les chemins et les paramètres.

## Emplacement du fichier de configuration

Le fichier de configuration est créé automatiquement au premier lancement dans :

```text
~/.config/cres-validation/config.ini
```

## Structure du fichier de configuration

```ini
[paths]
# Chemins vers les fichiers d'entrée (fichiers source .txt)
source_dir = ~/data/cres/validation/input/source

# Chemins vers les répertoires
output_dir = ~/data/cres/validation/output
log_dir = ~/data/cres/validation/logs
temp_dir = /tmp/cres-validation
```

## Sections de configuration

### Section `[paths]`

| Option       | Description                                      | Exemple                      |
|--------------|--------------------------------------------------|------------------------------|
| `source_dir` | Répertoire contenant les fichiers source .txt   | `~/data/cres/input/source`   |
| `output_dir` | Répertoire où écrire les fichiers corrigés       | `~/data/cres/output`         |
| `log_dir`    | Répertoire pour les fichiers de log              | `~/data/cres/logs`           |
| `temp_dir`   | Répertoire temporaire                            | `/tmp/cres-validation`       |

### Délimiteur CSV

Le délimiteur CSV est configuré via la variable d'environnement Python `CRES_CSV_DELIMITER` (accessible via `os.environ`). Si cette variable n'est pas définie, le délimiteur par défaut est `;` (point-virgule).

```python
import os

# Utiliser le délimiteur par défaut (;)
# (sans définir la variable d'environnement)

# Utiliser une virgule comme délimiteur
os.environ["CRES_CSV_DELIMITER"] = ","

# Utiliser un point-virgule explicitement
os.environ["CRES_CSV_DELIMITER"] = ";"
```

**Note:** Cette configuration pourra être étendue à l'avenir pour permettre un ajustement fichier par fichier.

## Chemins relatifs et absolus

Les chemins peuvent être spécifiés de plusieurs façons :

- **Chemins absolus** : `/home/user/data/input`
- **Chemins relatifs** : `./data/input`
- **Tilde expansion** : `~/data/input` (sera remplacé par `$HOME/data/input`)

## Exemple de configuration personnalisée

```ini
[paths]
source_dir = /mnt/data/cres/validation/input/source
output_dir = /mnt/data/cres/validation/output
log_dir = /var/log/cres-validation
temp_dir = /tmp/cres-validation
```

## Accès programmatique

```python
from cres_validation import get_config, get_delimiter

config = get_config()

# Récupérer un chemin
source_dir = config.get_path("paths", "source_dir")

# Récupérer le délimiteur depuis la variable d'environnement
delimiter = get_delimiter()  # Retourne ';' par défaut ou la valeur de CRES_CSV_DELIMITER
```

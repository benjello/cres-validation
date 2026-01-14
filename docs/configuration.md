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
# Chemins vers les fichiers d'entrée
input_dir = ~/data/cres/validation/input

# Chemins vers les répertoires
output_dir = ~/data/cres/validation/output
log_dir = ~/data/cres/validation/logs
temp_dir = /tmp/cres-validation
```

## Sections de configuration

### Section `[paths]`

| Option       | Description                                      | Exemple                |
|--------------|--------------------------------------------------|------------------------|
| `input_dir`  | Répertoire contenant les fichiers CSV à traiter  | `~/data/cres/input`    |
| `output_dir` | Répertoire où écrire les fichiers corrigés       | `~/data/cres/output`   |
| `log_dir`    | Répertoire pour les fichiers de log              | `~/data/cres/logs`     |
| `temp_dir`   | Répertoire temporaire                            | `/tmp/cres-validation` |

### Délimiteur CSV

Le délimiteur est **fixé à `;`** dans le code (pour éviter les problèmes lorsque des champs contiennent des virgules `,`).

## Chemins relatifs et absolus

Les chemins peuvent être spécifiés de plusieurs façons :

- **Chemins absolus** : `/home/user/data/input`
- **Chemins relatifs** : `./data/input`
- **Tilde expansion** : `~/data/input` (sera remplacé par `$HOME/data/input`)

## Exemple de configuration personnalisée

```ini
[paths]
input_dir = /mnt/data/cres/validation/input
output_dir = /mnt/data/cres/validation/output
log_dir = /var/log/cres-validation
temp_dir = /tmp/cres-validation
```

## Accès programmatique

```python
from cres_validation import get_config

config = get_config()

# Récupérer un chemin
input_dir = config.get_path("paths", "input_dir")

# Délimiteur fixe
delimiter = ";"
```

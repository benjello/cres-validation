# Installation

## Prérequis

- Python 3.13 ou supérieur
- [uv](https://github.com/astral-sh/uv) (gestionnaire de paquets Python)

## Installation avec uv

### 1. Cloner le repository

```bash
git clone https://github.com/benjello/cres-validation.git
cd cres-validation
```

### 2. Installer les dépendances

```bash
# Installer les dépendances principales
uv sync

# Installer avec les dépendances de développement (pour les tests)
uv sync --extra dev
```

### 3. Vérifier l'installation

```bash
# Exécuter les tests
uv run pytest tests/ -v

# Vérifier que le script fonctionne
uv run python main.py --help
```

## Installation alternative avec pip

Si vous préférez utiliser pip au lieu de uv :

```bash
pip install -e .
pip install -e ".[dev]"  # Pour les dépendances de développement
```

## Configuration initiale

Lors du premier lancement, le fichier de configuration sera créé automatiquement dans `~/.config/cres-validation/config.ini`.

Vous pouvez aussi créer un fichier `config.ini` dans le répertoire du projet comme template.

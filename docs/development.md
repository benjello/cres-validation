# Guide de développement

## Structure du projet

```
cres-validation/
├── cres_validation/        # Package principal
│   ├── __init__.py        # Exports publics
│   ├── config.py          # Module de configuration
│   ├── config.ini         # Template de configuration
│   ├── columns_number_validator.py # Module de validation/correction CSV
│   ├── colums_validator.py # Schémas Pandera
│   ├── validate_columns.py # Validation avec Pandera
│   └── convert_txt_to_csv.py # Conversion TXT → CSV
├── main.py                # Point d'entrée principal
├── pyproject.toml         # Configuration du projet
├── LICENSE                # Licence AGPL v3
├── tests/                 # Tests unitaires
│   ├── fixtures/         # Fichiers de test
│   │   ├── input/       # Fichiers d'entrée (source et csv)
│   │   ├── output/      # Fichiers de sortie attendus
│   │   └── logs/        # Logs générés lors des tests
│   ├── test_columns_validator.py  # Tests de validation/correction
│   ├── test_convert_txt_to_csv.py # Tests de conversion
│   └── test_performance.py        # Tests de performance
├── docs/                  # Documentation MkDocs
│   └── *.md
├── .github/workflows/     # CI/CD
│   ├── ci.yml
│   └── docs.yml
└── README.md
```

## Développement local

### Configuration de l'environnement

```bash
# Cloner le repository
git clone https://github.com/benjello/cres-validation.git
cd cres-validation

# Installer les dépendances de développement
uv sync --extra dev
```

### Exécuter les tests

```bash
# Tous les tests (rapides uniquement)
uv run pytest tests/ -v

# Inclure les tests de performance lents
uv run pytest tests/ -v -m slow

# Tests de performance uniquement
uv run pytest tests/test_performance.py -v

# Avec couverture
uv run pytest --cov=cres_validation.columns_number_validator tests/
```

**Note** : Les tests de performance génèrent des fichiers volumineux (1M lignes) à la volée, ils ne sont pas stockés dans le repository.

### Linting et formatage

Le projet utilise les outils Python standards. Vous pouvez ajouter :

- `ruff` pour le linting
- `black` pour le formatage
- `mypy` pour le type checking

## Contribution

### Workflow

1. Fork le repository
2. Créer une branche pour votre fonctionnalité : `git checkout -b feature/ma-fonctionnalite`
3. Faire vos modifications
4. Ajouter des tests pour les nouvelles fonctionnalités
5. Vérifier que tous les tests passent : `uv run pytest tests/ -v`
6. Commit vos changements : `git commit -m "Ajout de ma fonctionnalité"`
7. Push vers votre fork : `git push origin feature/ma-fonctionnalite`
8. Créer une Pull Request sur GitHub

### Standards de code

- Suivre PEP 8 pour le style de code
- Ajouter des docstrings pour toutes les fonctions publiques
- Écrire des tests pour les nouvelles fonctionnalités
- Mettre à jour la documentation si nécessaire

## Documentation

### Générer la documentation localement

```bash
# Installer MkDocs
uv sync --extra dev

# Servir la documentation localement
uv run mkdocs serve

# Construire la documentation
uv run mkdocs build
```

La documentation sera accessible sur `http://127.0.0.1:8000`

### Mettre à jour la documentation

1. Modifier les fichiers Markdown dans `docs/`
2. Vérifier localement avec `mkdocs serve`
3. Commit et push (la documentation sera déployée automatiquement sur GitHub Pages)

## CI/CD

Le projet utilise GitHub Actions pour :

- **Tests** : Exécution automatique des tests sur chaque push/PR
  - Tests rapides (20 tests) dans le job principal
  - Tests de performance lents (3 tests) dans un job séparé non bloquant
- **Linting** : Vérification de la syntaxe et des imports avec `ruff`
- **Documentation** : Déploiement automatique sur GitHub Pages

Voir `.github/workflows/ci.yml` et `.github/workflows/docs.yml` pour plus de détails.

### Optimisations CI

La CI est optimisée pour être rapide :
- Les tests lents (1M lignes) sont exécutés mais ne bloquent pas la CI
- Les fichiers de test volumineux sont générés à la volée (pas dans le repo)
- Les tests rapides sont exécutés en premier pour détecter rapidement les erreurs

## Release

Pour créer une nouvelle release :

1. Mettre à jour la version dans `pyproject.toml`
2. Créer un tag : `git tag v1.0.0`
3. Push le tag : `git push origin v1.0.0`
4. Créer une release sur GitHub

## Licence

Ce projet est sous licence [AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html). Toute contribution doit respecter cette licence.

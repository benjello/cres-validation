# Guide de développement

## Structure du projet

```
cres-validation/
├── config.py              # Module de configuration
├── csv_validator.py       # Module de validation/correction CSV
├── main.py                # Point d'entrée principal
├── config.ini             # Template de configuration
├── pyproject.toml         # Configuration du projet
├── LICENSE                # Licence AGPL v3
├── tests/                 # Tests unitaires
│   ├── fixtures/         # Fichiers de test
│   └── test_csv_validator.py
├── docs/                  # Documentation MkDocs
│   └── *.md
├── .github/workflows/     # CI/CD
│   └── ci.yml
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
# Tous les tests
uv run pytest tests/ -v

# Avec couverture
uv run pytest --cov=csv_validator tests/
```

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
- **Linting** : Vérification de la syntaxe et des imports
- **Documentation** : Déploiement automatique sur GitHub Pages

Voir `.github/workflows/ci.yml` et `.github/workflows/docs.yml` pour plus de détails.

## Release

Pour créer une nouvelle release :

1. Mettre à jour la version dans `pyproject.toml`
2. Créer un tag : `git tag v1.0.0`
3. Push le tag : `git push origin v1.0.0`
4. Créer une release sur GitHub

## Licence

Ce projet est sous licence [AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html). Toute contribution doit respecter cette licence.

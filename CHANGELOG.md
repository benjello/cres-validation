# Changelog

Tous les changements notables de ce projet seront documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Unreleased]

## [0.2.1] - 2026-01-14

### Ajouté
- Conversion CSV → Parquet et test de conformité CSV/Parquet

### Modifié
- Délimiteur par défaut : `;` (pour éviter les virgules dans les champs)
- Réorganisation des sorties de tests : `fixtures/output/csv/` et `fixtures/output/parquet/`

## [0.2.0] - 2026-01-13

### Ajouté
- Mesure de l'empreinte mémoire (RAM) dans les tests de performance avec `psutil`
- Fonctions helper pour mutualiser le code des tests (`prepare_test_csv`, `count_lines`)
- Test de validation du fichier de log (`test_log_file_created_and_has_content`)
- Documentation complète des tests de performance et de la mesure RAM
- CHANGELOG.md pour suivre les changements du projet

### Modifié
- Refactorisation des tests de performance pour réduire la duplication de code (~20% de code en moins)
- Correction des warnings Pandera en utilisant l'API recommandée (`pandera.pandas`)
- Amélioration de la documentation des tests et de l'API

### Corrigé
- Warnings de dépréciation Pandera (`FutureWarning`)
- Warnings de linting markdown dans la documentation

## [0.1.0] - 2026-01-13

### Ajouté
- Module `columns_number_validator` pour détecter et corriger les lignes avec un nombre de colonnes incorrect
- Module `convert_txt_to_csv` pour convertir les fichiers TXT vers CSV avec détection d'encodage
- Module `validate_columns` pour valider les colonnes avec les schémas Pandera
- Module `config` pour la gestion de la configuration via fichier INI
- Support des fichiers volumineux (millions de lignes) avec traitement optimisé en deux passes
- Traitement séparé du header (peut avoir une colonne supplémentaire)
- Ajustement automatique du header lors de la correction
- Logging configurable avec niveaux de verbosité (default, `-v`, `-vv`)
- Tests unitaires et tests de performance
- Documentation MkDocs avec déploiement automatique sur GitHub Pages
- CI/CD avec GitHub Actions
- Licence AGPL v3

### Modifié
- Structure du projet organisée en package Python (`cres_validation/`)

[Unreleased]: https://github.com/benjello/cres-validation/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/benjello/cres-validation/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/benjello/cres-validation/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/benjello/cres-validation/releases/tag/v0.1.0

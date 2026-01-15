import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from cres_validation import get_config
from cres_validation.columns_number_validator import correct_csv, csv_validate_columns_number
from cres_validation.columns_validator import validate_csv_columns
from cres_validation.convert_to_parquet import convert_csv_to_parquet
from cres_validation.convert_txt_to_csv import convert_txt_file_to_csv


def setup_logger(
    log_file: Path, verbose: int = 0, additional_log_file: Path | None = None
) -> logging.Logger:
    """
    Configure le logger avec les niveaux de verbosité.

    Args:
        log_file: Chemin vers le fichier de log principal
        verbose: Niveau de verbosité (0=WARNING, 1=INFO, 2=DEBUG)
        additional_log_file: Chemin optionnel vers un fichier de log supplémentaire

    Returns:
        Logger configuré
    """
    # Déterminer le niveau de log selon la verbosité
    if verbose >= 2:
        level = logging.DEBUG
    elif verbose >= 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    # Créer le logger
    logger = logging.getLogger("cres-validation")
    logger.setLevel(level)

    # Formatter pour les messages
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler pour le fichier principal (tous les niveaux)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Tout dans le fichier
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler pour le fichier de log supplémentaire si spécifié
    if additional_log_file:
        additional_file_handler = logging.FileHandler(additional_log_file, encoding="utf-8")
        additional_file_handler.setLevel(logging.DEBUG)  # Tout dans le fichier
        additional_file_handler.setFormatter(formatter)
        logger.addHandler(additional_file_handler)

    # Handler pour stdout (selon la verbosité)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def main():
    parser = argparse.ArgumentParser(description="Validation et correction de fichiers CSV")
    parser.add_argument(
        "--correct",
        action="store_true",
        help="Corriger les fichiers CSV en supprimant les retours à la ligne intempestifs",
    )
    parser.add_argument(
        "--test-fixtures",
        action="store_true",
        help="Utiliser les fixtures de test (tests/fixtures) au lieu de la configuration utilisateur",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Augmenter la verbosité (utiliser -v pour INFO, -vv pour DEBUG)",
    )
    args = parser.parse_args()

    # Réinitialiser la config globale pour éviter les problèmes de cache
    from cres_validation.config import reset_config
    reset_config()

    # Initialiser le lecteur de configuration
    if args.test_fixtures:
        # Utiliser le config.ini des tests pour pointer vers les fixtures
        project_root = Path(__file__).parent
        tests_config_path = project_root / "tests" / "config.ini"
        config = get_config(tests_config_path)
    else:
        # Utiliser la configuration utilisateur par défaut (~/.config/cres-validation/config.ini)
        config = get_config()  # Cherche config.ini automatiquement dans le home de l'utilisateur

    try:
        # Récupérer les chemins depuis la configuration
        source_dir = config.get_path("paths", "source_dir")
        output_dir = config.get_path("paths", "output_dir")
        log_dir = config.get_path("paths", "log_dir")

        # Créer le fichier de log avec la date ISO
        log_dir.mkdir(parents=True, exist_ok=True)
        date_iso = datetime.now().strftime("%Y-%m-%d")
        mode = "correction" if args.correct else "validation"
        log_file = log_dir / f"cres-validation-{mode}-{date_iso}.log"

        # Créer également un répertoire logs local s'il n'existe pas
        local_logs_dir = Path("logs")
        local_logs_dir.mkdir(parents=True, exist_ok=True)
        local_log_file = local_logs_dir / f"cres-validation-{mode}-{date_iso}.log"

        # Configurer le logger avec deux handlers de fichier
        logger = setup_logger(log_file, verbose=args.verbose, additional_log_file=local_log_file)

        logger.info("Hello from cres-validation!")
        logger.info(f"Répertoire source: {source_dir}")
        logger.info(f"Répertoire de sortie: {output_dir}")
        logger.info(f"Fichier de log principal: {log_file}")
        if local_log_file.exists():
            logger.info(f"Fichier de log local: {local_log_file}")
        logger.debug(f"Niveau de verbosité: {args.verbose} ({logging.getLevelName(logger.level)})")

        # Vérifier que le répertoire source existe
        if not source_dir.exists():
            logger.warning(f"Le répertoire {source_dir} n'existe pas")
            return

        if not source_dir.is_dir():
            logger.warning(f"{source_dir} n'est pas un répertoire")
            return

        # Trouver tous les fichiers TXT dans le répertoire
        txt_files = sorted(source_dir.glob("*.txt")) + sorted(source_dir.glob("*.TXT"))
        logger.debug(f"Recherche de fichiers TXT dans {source_dir}")

        if not txt_files:
            logger.warning(f"Aucun fichier TXT trouvé dans {source_dir}")
            return

        logger.info(f"{len(txt_files)} fichier(s) TXT trouvé(s)")

        # Convertir les fichiers TXT en CSV temporaires
        converted_files = []
        txt_to_csv_mapping = {}  # Mapping txt_file -> csv_file pour garder la trace
        # Créer un répertoire temporaire pour les CSV convertis
        temp_csv_dir = source_dir / "csv_temp"
        temp_csv_dir.mkdir(parents=True, exist_ok=True)

        for txt_file in txt_files:
            try:
                # Créer le nom du fichier CSV (remplacer espaces par _)
                csv_name = txt_file.stem.replace(" ", "_") + ".csv"
                csv_file = temp_csv_dir / csv_name
                logger.info(f"Conversion: {txt_file.name} → {csv_file.name}")
                convert_txt_file_to_csv(txt_file, csv_file, logger=logger)
                converted_files.append(csv_file)
                txt_to_csv_mapping[txt_file] = csv_file
            except Exception as e:
                logger.error(
                    f"Erreur lors de la conversion de {txt_file.name}: {e}",
                    exc_info=args.verbose >= 2,
                )

        if not converted_files:
            logger.warning("Aucun fichier TXT n'a pu être converti")
            return

        logger.info(f"{len(converted_files)} fichier(s) TXT converti(s) en CSV")
        if args.correct:
            logger.info("Mode correction activé")
        logger.info("=" * 60)

        # Délimiteur depuis la variable d'environnement Python (par défaut ';')
        from cres_validation.config import get_delimiter
        delimiter = get_delimiter()
        logger.debug(f"Délimiteur utilisé: '{delimiter}' (depuis os.environ['CRES_CSV_DELIMITER'] ou défaut)")

        # Suivi des résultats pour le résumé final
        files_ok = []  # Fichiers sans problème
        files_with_corrections = []  # Fichiers avec corrections
        files_with_warnings = []  # Fichiers avec warnings (validation Pandera)
        files_with_errors = []  # Fichiers avec erreurs

        # Traiter chaque fichier CSV converti
        for idx, csv_file in enumerate(converted_files, start=1):
            logger.info(f"[{idx}/{len(converted_files)}] Traitement de: {csv_file.name}")
            logger.debug(f"Chemin complet: {csv_file}")

            try:
                if args.correct:
                    # Mode correction : corriger le fichier
                    # Trouver le fichier TXT source correspondant
                    txt_source = None
                    for txt_file, mapped_csv in txt_to_csv_mapping.items():
                        if mapped_csv == csv_file:
                            txt_source = txt_file
                            break

                    # Nommer le fichier de sortie basé sur le fichier TXT source
                    source_name = txt_source.stem.replace(" ", "_") if txt_source else csv_file.stem

                    # Créer les répertoires de sortie
                    csv_output_dir = output_dir / "csv"
                    parquet_output_dir = output_dir / "parquet"
                    rejected_output_dir = output_dir / "rejected"
                    csv_output_dir.mkdir(parents=True, exist_ok=True)
                    parquet_output_dir.mkdir(parents=True, exist_ok=True)
                    rejected_output_dir.mkdir(parents=True, exist_ok=True)

                    # Créer le chemin pour les lignes rejetées
                    rejected_output_path = rejected_output_dir / f"rejected_{source_name}.csv"

                    # Sauvegarder le CSV corrigé
                    csv_output_file = csv_output_dir / f"corrected_{source_name}.csv"
                    logger.debug(f"Fichier CSV de sortie: {csv_output_file}")

                    # Analyser le fichier avant correction pour détecter les problèmes
                    from cres_validation.columns_number_validator import analyze_csv_columns
                    expected_cols, problematic_lines, _, problematic_lines_dict = analyze_csv_columns(
                        csv_file,
                        delimiter=delimiter,
                        encoding="utf-8",
                        use_most_frequent=True,
                        show_progress=False,
                        logger=logger,
                    )
                    corrections_needed = len(problematic_lines) > 0

                    # Sauvegarder les lignes rejetées (lignes avec moins de colonnes + lignes suivantes fusionnées)
                    if problematic_lines:
                        try:
                            rejected_lines = []
                            def collect_rejected_lines(file_path: Path, enc: str, expected: int, problematic: list):
                                nonlocal rejected_lines
                                rejected_lines = []
                                all_lines = []
                                with open(file_path, encoding=enc, newline="", buffering=8192 * 16) as f:
                                    for line_num, line in enumerate(f, start=1):
                                        all_lines.append((line_num, line))

                                # Identifier les lignes avec MOINS de colonnes que prévu (qui seront fusionnées)

                                # Identifier les lignes qui seront fusionnées
                                # On veut garder toutes les lignes problématiques consécutives, chaque ligne une seule fois
                                # Les lignes seront groupées par paires dans le fichier (ligne N + ligne N+1)
                                problematic_set = set(problematic)
                                seen_line_nums = set()  # Pour éviter les doublons

                                # Parcourir toutes les lignes dans l'ordre et ajouter les lignes problématiques
                                # Pour chaque ligne problématique, ajouter cette ligne et la suivante (si elle est aussi problématique)
                                for idx in range(len(all_lines)):
                                    line_num, line = all_lines[idx]

                                    if line_num in problematic_set:
                                        # Ajouter cette ligne si elle n'a pas déjà été ajoutée
                                        if line_num not in seen_line_nums:
                                            rejected_lines.append((line_num, line))
                                            seen_line_nums.add(line_num)

                                        # Ajouter la ligne suivante si elle existe et est aussi problématique
                                        if idx + 1 < len(all_lines):
                                            next_line_num, next_line = all_lines[idx + 1]
                                            if next_line_num in problematic_set and next_line_num not in seen_line_nums:
                                                rejected_lines.append((next_line_num, next_line))
                                                seen_line_nums.add(next_line_num)

                            try:
                                collect_rejected_lines(csv_file, "utf-8", expected_cols, problematic_lines)
                            except UnicodeDecodeError:
                                collect_rejected_lines(csv_file, "latin-1", expected_cols, problematic_lines)

                            if rejected_lines:
                                from cres_validation.rejected_lines import (
                                    save_rejected_lines_to_csv,
                                )
                                save_rejected_lines_to_csv(
                                    csv_file,
                                    rejected_lines,
                                    rejected_output_path,
                                    delimiter=delimiter,
                                    encoding="utf-8",
                                    logger=logger,
                                )
                        except Exception as e:
                            logger.warning(f"Erreur lors de la sauvegarde des lignes rejetées: {e}", exc_info=args.verbose >= 2)

                    correct_csv(
                        csv_file,
                        csv_output_file,
                        delimiter=delimiter,
                        show_progress=args.verbose >= 1,
                        logger=logger,
                    )
                    logger.info(f"✅ Fichier CSV corrigé sauvegardé: {csv_output_file.name}")

                    # Valider les colonnes avec Pandera (types, formats, dates)
                    logger.info("Validation des colonnes avec Pandera...")
                    validation_success = False
                    validation_error = False
                    has_pandera_warnings = False

                    # Capturer les warnings émis pendant la validation
                    warning_messages = []

                    def make_warning_handler(messages_list):
                        class WarningCaptureHandler(logging.Handler):
                            def emit(self, record):
                                if record.levelno >= logging.WARNING:
                                    messages_list.append(record.getMessage())

                        return WarningCaptureHandler()

                    warning_handler = make_warning_handler(warning_messages)

                    logger.addHandler(warning_handler)

                    # Créer le chemin pour les lignes rejetées
                    rejected_output_path = rejected_output_dir / f"rejected_{source_name}.csv"

                    try:
                        validation_success = validate_csv_columns(
                            csv_output_file,
                            delimiter=delimiter,
                            schema_name="cnrps",
                            logger=logger,
                            rejected_output_path=rejected_output_path,
                        )
                        if validation_success:
                            if warning_messages:
                                has_pandera_warnings = True
                                logger.info(f"✅ Validation Pandera réussie pour {txt_source.name if txt_source else csv_file.name} : toutes les colonnes sont valides (avec warnings)")
                            else:
                                logger.info(f"✅ Validation Pandera réussie pour {txt_source.name if txt_source else csv_file.name} : toutes les colonnes sont valides")
                        else:
                            logger.warning(f"⚠️  Validation Pandera échouée pour {txt_source.name if txt_source else csv_file.name} : certaines colonnes ne respectent pas le schéma")
                            validation_error = True
                    except Exception as e:
                        logger.warning(f"⚠️  Erreur lors de la validation Pandera pour {txt_source.name if txt_source else csv_file.name}: {e}", exc_info=args.verbose >= 2)
                        validation_error = True
                    finally:
                        logger.removeHandler(warning_handler)

                    # Enregistrer le statut du fichier
                    source_file_name = txt_source.name if txt_source else csv_file.name
                    if (validation_error or has_pandera_warnings) and source_file_name not in files_with_warnings:
                        files_with_warnings.append(source_file_name)
                    if corrections_needed and source_file_name not in files_with_corrections:
                        files_with_corrections.append(source_file_name)
                    # Un fichier peut être à la fois avec corrections et warnings
                    if not validation_error and not has_pandera_warnings and not corrections_needed:
                        files_ok.append(source_file_name)

                    # Convertir en Parquet
                    parquet_output_file = parquet_output_dir / f"corrected_{source_name}.parquet"
                    logger.debug(f"Fichier Parquet de sortie: {parquet_output_file}")
                    convert_csv_to_parquet(
                        csv_output_file,
                        parquet_output_file,
                        delimiter=delimiter,
                        logger=logger,
                    )
                    logger.info(f"✅ Fichier Parquet sauvegardé: {parquet_output_file.name}")
                else:
                    # Mode validation : valider le fichier
                    # Trouver le fichier TXT source correspondant pour le nom
                    txt_source = None
                    for txt_file, mapped_csv in txt_to_csv_mapping.items():
                        if mapped_csv == csv_file:
                            txt_source = txt_file
                            break

                    source_file_name = txt_source.name if txt_source else csv_file.name
                    source_name = txt_source.stem.replace(" ", "_") if txt_source else csv_file.stem

                    # Créer le répertoire rejected si nécessaire
                    rejected_output_dir = output_dir / "rejected"
                    rejected_output_dir.mkdir(parents=True, exist_ok=True)
                    rejected_output_path = rejected_output_dir / f"rejected_{source_name}.csv"

                    csv_validate_columns_number(
                        csv_file,
                        delimiter=delimiter,
                        show_progress=args.verbose >= 1,
                        logger=logger,
                        rejected_output_path=rejected_output_path,
                    )

                    # Valider aussi les colonnes avec Pandera (types, formats, dates)
                    logger.info("Validation des colonnes avec Pandera...")
                    validation_success = False
                    validation_error = False
                    has_pandera_warnings = False

                    # Capturer les warnings émis pendant la validation
                    warning_messages = []

                    def make_warning_handler(messages_list):
                        class WarningCaptureHandler(logging.Handler):
                            def emit(self, record):
                                if record.levelno >= logging.WARNING:
                                    messages_list.append(record.getMessage())

                        return WarningCaptureHandler()

                    warning_handler = make_warning_handler(warning_messages)

                    logger.addHandler(warning_handler)

                    try:
                        validation_success = validate_csv_columns(
                            csv_file,
                            delimiter=delimiter,
                            schema_name="cnrps",
                            logger=logger,
                            rejected_output_path=rejected_output_path,
                        )
                        if validation_success:
                            if warning_messages:
                                has_pandera_warnings = True
                                logger.info(f"✅ Validation Pandera réussie pour {source_file_name} : toutes les colonnes sont valides (avec warnings)")
                            else:
                                logger.info(f"✅ Validation Pandera réussie pour {source_file_name} : toutes les colonnes sont valides")
                        else:
                            logger.warning(f"⚠️  Validation Pandera échouée pour {source_file_name} : certaines colonnes ne respectent pas le schéma")
                            validation_error = True
                    except Exception as e:
                        logger.warning(f"⚠️  Erreur lors de la validation Pandera pour {source_file_name}: {e}", exc_info=args.verbose >= 2)
                        validation_error = True
                    finally:
                        logger.removeHandler(warning_handler)

                    # Enregistrer le statut du fichier
                    if (validation_error or has_pandera_warnings) and source_file_name not in files_with_warnings:
                        files_with_warnings.append(source_file_name)
                    if not validation_error and not has_pandera_warnings:
                        files_ok.append(source_file_name)
            except Exception as e:
                # Trouver le fichier TXT source correspondant pour le nom
                txt_source = None
                for txt_file, mapped_csv in txt_to_csv_mapping.items():
                    if mapped_csv == csv_file:
                        txt_source = txt_file
                        break
                source_file_name = txt_source.name if txt_source else csv_file.name
                files_with_errors.append(source_file_name)
                logger.error(
                    f"Erreur lors du traitement de {source_file_name}: {e}", exc_info=args.verbose >= 2
                )

        # Nettoyer les fichiers CSV temporaires convertis
        if converted_files:
            logger.debug("Nettoyage des fichiers CSV temporaires...")
            for csv_file in converted_files:
                try:
                    csv_file.unlink()
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {csv_file.name}: {e}")
            # Supprimer le répertoire temporaire s'il est vide
            from contextlib import suppress

            with suppress(Exception):
                temp_csv_dir.rmdir()  # Le répertoire n'est pas vide ou n'existe pas

        logger.info("=" * 60)

        # Afficher le résumé final
        logger.info("")
        logger.info("=" * 60)
        logger.info("RÉSUMÉ FINAL")
        logger.info("=" * 60)

        total_files = len(converted_files)

        if files_ok:
            logger.info(f"✅ Fichiers traités sans problème ({len(files_ok)}/{total_files}):")
            for file_name in files_ok:
                logger.info(f"   • {file_name}")

        if files_with_corrections:
            logger.info("")
            logger.info(f"🔧 Fichiers avec corrections ({len(files_with_corrections)}/{total_files}):")
            for file_name in files_with_corrections:
                logger.info(f"   • {file_name}")

        if files_with_warnings:
            logger.info("")
            logger.info(f"⚠️  Fichiers avec warnings (validation Pandera) ({len(files_with_warnings)}/{total_files}):")
            for file_name in files_with_warnings:
                logger.info(f"   • {file_name}")

        if files_with_errors:
            logger.info("")
            logger.error(f"❌ Fichiers avec erreurs ({len(files_with_errors)}/{total_files}):")
            for file_name in files_with_errors:
                logger.error(f"   • {file_name}")

        logger.info("")
        logger.info("=" * 60)
        if args.correct:
            logger.info(f"Correction terminée pour {total_files} fichier(s) TXT")
        else:
            logger.info(f"Validation terminée pour {total_files} fichier(s) TXT")
        logger.info("=" * 60)

    except KeyError as e:
        logging.error(f"Erreur de configuration: {e}")
    except FileNotFoundError as e:
        logging.error(f"Erreur: {e}")


if __name__ == "__main__":
    main()

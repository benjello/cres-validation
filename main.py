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
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Augmenter la verbosité (utiliser -v pour INFO, -vv pour DEBUG)",
    )
    args = parser.parse_args()

    # Initialiser le lecteur de configuration
    config = get_config()  # Cherche config.ini automatiquement
    # Ou spécifier un chemin: config = get_config(Path("/chemin/vers/config.ini"))

    try:
        # Récupérer les chemins depuis la configuration
        input_dir = config.get_path("paths", "input_dir")
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
        logger.info(f"Répertoire d'entrée: {input_dir}")
        logger.info(f"Répertoire de sortie: {output_dir}")
        logger.info(f"Fichier de log principal: {log_file}")
        if local_log_file.exists():
            logger.info(f"Fichier de log local: {local_log_file}")
        logger.debug(f"Niveau de verbosité: {args.verbose} ({logging.getLevelName(logger.level)})")

        # Vérifier que le répertoire d'entrée existe
        if not input_dir.exists():
            logger.warning(f"Le répertoire {input_dir} n'existe pas")
            return

        if not input_dir.is_dir():
            logger.warning(f"{input_dir} n'est pas un répertoire")
            return

        # Trouver tous les fichiers TXT dans le répertoire
        txt_files = sorted(input_dir.glob("*.txt")) + sorted(input_dir.glob("*.TXT"))
        logger.debug(f"Recherche de fichiers TXT dans {input_dir}")

        if not txt_files:
            logger.warning(f"Aucun fichier TXT trouvé dans {input_dir}")
            return

        logger.info(f"{len(txt_files)} fichier(s) TXT trouvé(s)")

        # Convertir les fichiers TXT en CSV temporaires
        converted_files = []
        txt_to_csv_mapping = {}  # Mapping txt_file -> csv_file pour garder la trace
        # Créer un répertoire temporaire pour les CSV convertis
        temp_csv_dir = input_dir / "csv_temp"
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

        # Délimiteur fixe : point-virgule (pour éviter les problèmes avec les virgules dans les strings)
        delimiter = ";"
        logger.debug(f"Délimiteur utilisé: '{delimiter}'")

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
                    csv_output_dir.mkdir(parents=True, exist_ok=True)
                    parquet_output_dir.mkdir(parents=True, exist_ok=True)

                    # Sauvegarder le CSV corrigé
                    csv_output_file = csv_output_dir / f"corrected_{source_name}.csv"
                    logger.debug(f"Fichier CSV de sortie: {csv_output_file}")
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
                    try:
                        validation_success = validate_csv_columns(
                            csv_output_file,
                            delimiter=delimiter,
                            schema_name="cnrps",
                            logger=logger,
                        )
                        if validation_success:
                            logger.info("✅ Validation Pandera réussie : toutes les colonnes sont valides")
                        else:
                            logger.warning("⚠️  Validation Pandera échouée : certaines colonnes ne respectent pas le schéma")
                    except Exception as e:
                        logger.warning(f"⚠️  Erreur lors de la validation Pandera: {e}", exc_info=args.verbose >= 2)

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
                    csv_validate_columns_number(
                        csv_file,
                        delimiter=delimiter,
                        show_progress=args.verbose >= 1,
                        logger=logger,
                    )

                    # Valider aussi les colonnes avec Pandera (types, formats, dates)
                    logger.info("Validation des colonnes avec Pandera...")
                    try:
                        validation_success = validate_csv_columns(
                            csv_file,
                            delimiter=delimiter,
                            schema_name="cnrps",
                            logger=logger,
                        )
                        if validation_success:
                            logger.info("✅ Validation Pandera réussie : toutes les colonnes sont valides")
                        else:
                            logger.warning("⚠️  Validation Pandera échouée : certaines colonnes ne respectent pas le schéma")
                    except Exception as e:
                        logger.warning(f"⚠️  Erreur lors de la validation Pandera: {e}", exc_info=args.verbose >= 2)
            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement de {csv_file.name}: {e}", exc_info=args.verbose >= 2
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
        if args.correct:
            logger.info(f"Correction terminée pour {len(converted_files)} fichier(s) TXT")
        else:
            logger.info(f"Validation terminée pour {len(converted_files)} fichier(s) TXT")

    except KeyError as e:
        logging.error(f"Erreur de configuration: {e}")
    except FileNotFoundError as e:
        logging.error(f"Erreur: {e}")


if __name__ == "__main__":
    main()

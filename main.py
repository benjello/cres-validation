import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from cres_validation import get_config
from cres_validation.columns_number_validator import correct_csv, validate_csv


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

        # Trouver tous les fichiers CSV dans le répertoire
        csv_files = sorted(input_dir.glob("*.csv"))
        logger.debug(f"Recherche de fichiers CSV dans {input_dir}")

        if not csv_files:
            logger.warning(f"Aucun fichier CSV trouvé dans {input_dir}")
            return

        logger.info(f"{len(csv_files)} fichier(s) CSV trouvé(s)")
        if args.correct:
            logger.info("Mode correction activé")
        logger.info("=" * 60)

        # Récupérer le délimiteur depuis la config (par défaut ";")
        delimiter = config.get("csv", "delimiter", fallback=",")
        logger.debug(f"Délimiteur utilisé: '{delimiter}'")

        # Traiter chaque fichier CSV
        for idx, csv_file in enumerate(csv_files, start=1):
            logger.info(f"[{idx}/{len(csv_files)}] Traitement de: {csv_file.name}")
            logger.debug(f"Chemin complet: {csv_file}")

            try:
                if args.correct:
                    # Mode correction : corriger le fichier
                    # Nommer le fichier de sortie: corrected_{nom_sans_extension}.csv
                    source_name = csv_file.stem  # Nom sans extension
                    output_file = output_dir / f"corrected_{source_name}.csv"
                    logger.debug(f"Fichier de sortie: {output_file}")
                    correct_csv(
                        csv_file,
                        output_file,
                        delimiter=delimiter,
                        show_progress=args.verbose >= 1,
                        logger=logger,
                    )
                else:
                    # Mode validation : valider le fichier
                    validate_csv(
                        csv_file,
                        delimiter=delimiter,
                        show_progress=args.verbose >= 1,
                        logger=logger,
                    )
            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement de {csv_file.name}: {e}", exc_info=args.verbose >= 2
                )

        logger.info("=" * 60)
        if args.correct:
            logger.info(f"Correction terminée pour {len(csv_files)} fichier(s)")
        else:
            logger.info(f"Validation terminée pour {len(csv_files)} fichier(s)")

    except KeyError as e:
        logging.error(f"Erreur de configuration: {e}")
    except FileNotFoundError as e:
        logging.error(f"Erreur: {e}")


if __name__ == "__main__":
    main()

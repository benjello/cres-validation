"""Script pour convertir les fichiers .txt du répertoire source en .csv dans le répertoire csv"""

import logging
from pathlib import Path

import chardet

from cres_validation.config import get_config


def detect_encoding(file_path: Path) -> str:
    """
    Détecte l'encodage d'un fichier texte.

    Args:
        file_path: Chemin vers le fichier

    Returns:
        Encodage détecté (par défaut 'utf-8')
    """
    # Lire un échantillon du fichier pour détecter l'encodage
    with open(file_path, "rb") as f:
        raw_data = f.read(10000)  # Lire les 10 premiers KB

    if not raw_data:
        return "utf-8"

    # Détecter l'encodage avec chardet
    result = chardet.detect(raw_data)
    encoding = result.get("encoding", "utf-8")
    confidence = result.get("confidence", 0)

    # Si la confiance est faible, essayer utf-8 en premier
    if confidence < 0.7:
        try:
            with open(file_path, encoding="utf-8") as f:
                f.read()
            return "utf-8"
        except UnicodeDecodeError:
            pass

    # Essayer l'encodage détecté
    try:
        with open(file_path, encoding=encoding) as f:
            f.read()
        return encoding
    except (UnicodeDecodeError, LookupError):
        # Si l'encodage détecté ne fonctionne pas, essayer latin-1 (qui accepte tous les bytes)
        return "latin-1"


def convert_txt_to_csv(
    source_dir: Path, csv_dir: Path, logger: logging.Logger | None = None
) -> None:
    """
    Convertit tous les fichiers .txt du répertoire source en .csv dans le répertoire csv.

    Args:
        source_dir: Répertoire contenant les fichiers .txt
        csv_dir: Répertoire de destination pour les fichiers .csv
        logger: Logger optionnel pour les messages (si None, utilise print)
    """
    # Utiliser un logger par défaut si aucun n'est fourni
    if logger is None:
        logger = logging.getLogger("cres-validation.convert")
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    if not source_dir.exists():
        logger.warning(f"Le répertoire source n'existe pas: {source_dir}")
        return

    if not source_dir.is_dir():
        logger.warning(f"{source_dir} n'est pas un répertoire")
        return

    # Créer le répertoire de destination s'il n'existe pas
    csv_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Répertoire de destination: {csv_dir}")

    # Trouver tous les fichiers .txt
    txt_files = sorted(source_dir.glob("*.txt"))
    txt_files.extend(sorted(source_dir.glob("*.TXT")))  # Aussi les fichiers en majuscules

    if not txt_files:
        logger.info(f"Aucun fichier .txt trouvé dans {source_dir}")
        return

    logger.info(f"{len(txt_files)} fichier(s) .txt trouvé(s) dans {source_dir}")
    logger.debug("=" * 60)

    for txt_file in txt_files:
        # Détecter l'encodage
        encoding = detect_encoding(txt_file)
        logger.info(f"Fichier: {txt_file.name}")
        logger.debug(f"Encodage détecté: {encoding}")

        # Créer le nouveau nom de fichier (remplacer espaces par _ et changer extension)
        new_name = txt_file.stem.replace(" ", "_") + ".csv"
        csv_file = csv_dir / new_name

        try:
            # Lire le fichier avec l'encodage détecté
            with open(txt_file, encoding=encoding) as infile:
                content = infile.read()

            # Remplacer les délimiteurs ; par , (sans corriger les lignes incomplètes)
            content = content.replace(";", ",")

            # Écrire en UTF-8 dans le fichier CSV
            with open(csv_file, "w", encoding="utf-8") as outfile:
                outfile.write(content)

            original_size = txt_file.stat().st_size
            new_size = csv_file.stat().st_size
            logger.info(f"Converti: {csv_file.name}")
            logger.debug(f"Taille: {original_size:,} bytes → {new_size:,} bytes")

        except Exception as e:
            logger.error(f"Erreur lors de la conversion de {txt_file.name}: {e}", exc_info=True)

    logger.info("=" * 60)
    logger.info(f"Conversion terminée: {len(txt_files)} fichier(s) traité(s)")


if __name__ == "__main__":
    # Configurer un logger pour le script standalone
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("cres-validation.convert")

    config = get_config()
    input_dir = config.get_path("paths", "input_dir")
    source_dir = input_dir / "source"
    csv_dir = input_dir / "csv"

    logger.info(f"Répertoire source: {source_dir}")
    logger.info(f"Répertoire CSV: {csv_dir}")

    convert_txt_to_csv(source_dir, csv_dir, logger=logger)

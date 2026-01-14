"""Configuration partagée pour tous les tests"""

import logging
from datetime import datetime
from pathlib import Path

import pytest

# Chemin vers les fichiers de test dans fixtures
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
LOGS_DIR = FIXTURES_DIR / "logs"
SOURCE_DIR = FIXTURES_DIR / "input" / "source"
CSV_DIR = FIXTURES_DIR / "input" / "csv"


class FileNameFilter(logging.Filter):
    """Filtre pour diriger les messages vers le bon fichier de log en fonction du nom du fichier dans le message"""

    def __init__(self, file_name: str):
        super().__init__()
        self.file_name = file_name
        # Messages généraux à inclure dans tous les logs
        self.general_messages = [
            "fichier(s) .txt trouvé(s)",
            "Répertoire de destination",
            "Conversion terminée",
            "=" * 60,  # Séparateur
        ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filtre les messages qui concernent ce fichier spécifique ou sont généraux"""
        message = record.getMessage()

        # Inclure les messages généraux
        if any(general_msg in message for general_msg in self.general_messages):
            return True

        # Accepter tous les messages de validation Pandera (ils concernent le fichier)
        # car ils sont générés dans le contexte de validation d'un fichier spécifique
        # après le message initial "Validation du fichier: ..." qui contient le nom du fichier
        if "Validation" in message or "Pandera" in message or "schéma" in message.lower():
            return True

        # Accepter les messages de préparation/lecture qui suivent une validation
        # (ils sont dans le même contexte de validation)
        if any(keyword in message for keyword in ["Lecture du fichier", "Header détecté", "Préparation des données", "colonnes", "Conversion des dates"]):
            # Vérifier si le logger est dans le contexte de validation
            if "cres-validation" in record.name or "pandera" in record.name.lower():
                return True

        # Vérifier si le message contient le nom du fichier (avec ou sans espaces)
        file_name_with_spaces = self.file_name.replace("_", " ")
        # Le nom du fichier peut être avec ou sans espaces, et peut être mentionné
        # dans le chemin complet (pour les messages de validation qui mentionnent le CSV)
        # Accepter si le nom du fichier apparaît n'importe où dans le message
        return (
            self.file_name in message
            or file_name_with_spaces in message
            # Accepter aussi si le message contient le nom du fichier dans un chemin
            or f"/{self.file_name}" in message
            or f"/{file_name_with_spaces}" in message
            or f"\\{self.file_name}" in message  # Pour Windows
            or f"\\{file_name_with_spaces}" in message  # Pour Windows
        )


@pytest.fixture(scope="session", autouse=True)
def setup_unified_logger():
    """Configure les loggers pour capturer tous les logs avec un log par fichier source"""
    # Créer le répertoire de logs s'il n'existe pas
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Formatter partagé
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Trouver tous les fichiers .txt dans le répertoire source
    txt_files = sorted(SOURCE_DIR.glob("*.txt"))
    txt_files.extend(sorted(SOURCE_DIR.glob("*.TXT")))

    if not txt_files:
        # Si aucun fichier TXT n'est trouvé, ne pas créer de logs
        yield []
        return

    # Créer un handler de log pour chaque fichier source
    log_files = []
    handlers = []

    # Logger pour columns_number_validator
    columns_logger = logging.getLogger("cres-validation")
    columns_logger.setLevel(logging.DEBUG)
    columns_logger.propagate = False

    # Logger pour convert_txt_to_csv
    convert_logger = logging.getLogger("cres-validation.convert")
    convert_logger.setLevel(logging.DEBUG)
    convert_logger.propagate = False

    # Logger pour validate_csv_columns (Pandera)
    pandera_logger = logging.getLogger("cres-validation.pandera")
    pandera_logger.setLevel(logging.DEBUG)
    pandera_logger.propagate = False

    date_part = datetime.now().strftime("%Y_%m_%d")
    time_part = datetime.now().strftime("%H_%M_%S")

    for txt_file in txt_files:
        # Créer un fichier de log avec nom du fichier et timestamp lisible
        # Format: nom_du_fichier-date-heure.log
        file_name = txt_file.stem.replace(" ", "_")
        log_file = LOGS_DIR / f"{file_name}-{date_part}-{time_part}.log"

        # Handler pour ce fichier spécifique avec un filtre
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        # Ajouter un filtre pour ne garder que les messages concernant ce fichier
        file_handler.addFilter(FileNameFilter(file_name))

        # Ajouter le handler aux trois loggers
        columns_logger.addHandler(file_handler)
        convert_logger.addHandler(file_handler)
        pandera_logger.addHandler(file_handler)

        log_files.append(log_file)
        handlers.append(file_handler)

    yield log_files

    # Nettoyer après les tests
    for handler in handlers:
        handler.close()
        columns_logger.removeHandler(handler)
        convert_logger.removeHandler(handler)
        pandera_logger.removeHandler(handler)

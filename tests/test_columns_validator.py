"""Tests pour le module columns_number_validator"""
import logging
from datetime import datetime
from pathlib import Path

import pytest

from cres_validation.columns_number_validator import analyze_csv_columns, correct_csv, validate_csv

# Chemin vers les fichiers de test dans fixtures
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
INPUT_FILE = FIXTURES_DIR / "input" / "csv" / "echantillon_cnrps_pb_fondation_fidaa.csv"
# Le fichier de sortie attendu suit le format: corrected_{nom_source}.csv
EXPECTED_OUTPUT_FILE = FIXTURES_DIR / "output" / f"corrected_{INPUT_FILE.stem}.csv"
LOGS_DIR = FIXTURES_DIR / "logs"
DELIMITER = ','


@pytest.fixture(scope="session", autouse=True)
def setup_test_logger():
    """Configure les loggers pour capturer les logs des modules de traitement"""
    # Créer le répertoire de logs s'il n'existe pas
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Créer un fichier de log avec nom du fichier et timestamp lisible
    # Format: nom_du_fichier-date-heure.log (ex: echantillon_cnrps_pb_fondation_fidaa-2026_01_13-13_02_28.log)
    file_name = INPUT_FILE.stem  # Nom du fichier sans extension
    date_part = datetime.now().strftime("%Y_%m_%d")
    time_part = datetime.now().strftime("%H_%M_%S")
    log_file = LOGS_DIR / f"{file_name}-{date_part}-{time_part}.log"

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler pour le fichier (partagé par tous les loggers)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Configurer les loggers des modules de traitement pour écrire dans le fichier
    # Logger pour columns_number_validator
    columns_logger = logging.getLogger('cres-validation')
    columns_logger.setLevel(logging.DEBUG)
    columns_logger.addHandler(file_handler)
    columns_logger.propagate = False  # Ne pas propager vers le root logger

    # Logger pour convert_txt_to_csv
    convert_logger = logging.getLogger('cres-validation.convert')
    convert_logger.setLevel(logging.DEBUG)
    convert_logger.addHandler(file_handler)
    convert_logger.propagate = False

    yield log_file

    # Nettoyer après les tests
    for logger in [columns_logger, convert_logger]:
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


@pytest.fixture
def test_logger():
    """Retourne le logger pour les modules de traitement (pas pour les tests)"""
    return logging.getLogger('cres-validation')


@pytest.fixture
def output_file(tmp_path):
    """Crée un fichier de sortie temporaire pour les tests de correction"""
    source_name = INPUT_FILE.stem
    return tmp_path / f"corrected_{source_name}.csv"


def test_input_file_exists():
    """Vérifie que le fichier d'entrée de test existe"""
    assert INPUT_FILE.exists(), f"Le fichier de test {INPUT_FILE} n'existe pas"


def test_expected_output_file_exists():
    """Vérifie que le fichier de sortie attendu existe"""
    assert EXPECTED_OUTPUT_FILE.exists(), f"Le fichier de test {EXPECTED_OUTPUT_FILE} n'existe pas"


def test_analyze_csv_columns(test_logger):
    """Test de l'analyse des colonnes du fichier d'entrée"""
    expected_cols, problematic_lines, column_counter, problematic_lines_dict = analyze_csv_columns(
        INPUT_FILE,
        delimiter=DELIMITER,
        show_progress=False,
        logger=test_logger
    )

    # Vérifier que le nombre de colonnes attendu est détecté
    assert expected_cols > 0, "Le nombre de colonnes attendu doit être > 0"

    # Vérifier qu'il y a des lignes problématiques (c'est le but du fichier de test)
    assert len(problematic_lines) > 0, "Le fichier de test doit contenir des lignes problématiques"

    # Vérifier que le compteur contient des données
    assert len(column_counter) > 0, "Le compteur de colonnes doit contenir des données"


def test_validate_csv(test_logger):
    """Test de la validation du fichier CSV"""
    # Cette fonction ne fait que logger, on vérifie qu'elle ne lève pas d'exception
    try:
        validate_csv(
            INPUT_FILE,
            delimiter=DELIMITER,
            show_progress=False,
            logger=test_logger
        )
    except Exception as e:
        pytest.fail(f"validate_csv a levé une exception: {e}")


def test_correct_csv(output_file, test_logger):
    """Test de la correction du fichier CSV"""
    # Corriger le fichier (les logs seront capturés automatiquement)
    correct_csv(
        INPUT_FILE,
        output_file,
        delimiter=DELIMITER,
        show_progress=False,
        logger=test_logger
    )

    # Vérifier que le fichier de sortie a été créé
    assert output_file.exists(), "Le fichier corrigé doit être créé"

    # Vérifier que le fichier n'est pas vide
    file_size = output_file.stat().st_size
    assert file_size > 0, "Le fichier corrigé ne doit pas être vide"

    # Comparer avec le fichier attendu
    with open(output_file, encoding='utf-8') as f1, \
         open(EXPECTED_OUTPUT_FILE, encoding='utf-8') as f2:
        lines1 = [line.strip() for line in f1 if line.strip()]
        lines2 = [line.strip() for line in f2 if line.strip()]

    assert len(lines1) == len(lines2), \
        f"Le nombre de lignes diffère: {len(lines1)} vs {len(lines2)}"

    # Vérifier que toutes les lignes ont le même nombre de colonnes que le fichier attendu
    for i, (line1, line2) in enumerate(zip(lines1, lines2, strict=True), start=1):
        cols1 = line1.count(DELIMITER) + 1
        cols2 = line2.count(DELIMITER) + 1
        assert cols1 == cols2, \
            f"Ligne {i}: nombre de colonnes différent ({cols1} vs {cols2})"

    # Vérifier que toutes les lignes de données ont le bon nombre de colonnes
    expected_cols, _, _, _ = analyze_csv_columns(INPUT_FILE, delimiter=DELIMITER, show_progress=False)

    # Le header peut avoir un nombre de colonnes différent, on vérifie à partir de la ligne 2
    data_lines = lines1[1:] if len(lines1) > 1 and lines1[0].startswith(',matricul') else lines1
    for i, line in enumerate(data_lines, start=2 if len(lines1) > 1 and lines1[0].startswith(',matricul') else 1):
        cols = line.count(DELIMITER) + 1
        assert cols == expected_cols, \
            f"Ligne {i}: {cols} colonnes au lieu de {expected_cols}"


def test_correct_csv_reduces_line_count(output_file, test_logger):
    """Test que la correction réduit le nombre de lignes en fusionnant les lignes incomplètes"""
    # Compter les lignes dans le fichier original
    with open(INPUT_FILE, encoding='utf-8') as f:
        original_lines = sum(1 for line in f if line.strip())

    # Corriger le fichier (les logs seront capturés automatiquement)
    correct_csv(
        INPUT_FILE,
        output_file,
        delimiter=DELIMITER,
        show_progress=False,
        logger=test_logger
    )

    # Compter les lignes dans le fichier corrigé
    with open(output_file, encoding='utf-8') as f:
        corrected_lines = sum(1 for line in f if line.strip())

    # Le fichier corrigé doit avoir moins ou autant de lignes que l'original
    assert corrected_lines <= original_lines, \
        f"Le fichier corrigé ne devrait pas avoir plus de lignes ({corrected_lines} vs {original_lines})"

    # Dans notre cas de test, on sait qu'il y a des lignes à fusionner
    assert corrected_lines < original_lines, \
        f"Le fichier de test devrait avoir des lignes fusionnées ({corrected_lines} vs {original_lines})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

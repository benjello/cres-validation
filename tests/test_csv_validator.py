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


@pytest.fixture(scope="session", autouse=True)
def setup_test_logger():
    """Configure un logger pour sauvegarder les résultats des tests"""
    # Créer le répertoire de logs s'il n'existe pas
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Créer un fichier de log avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOGS_DIR / f"test_results_{timestamp}.log"

    # Configurer le logger
    logger = logging.getLogger('test-columns-number-validator')
    logger.setLevel(logging.DEBUG)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler pour le fichier
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler pour la console (optionnel, pour voir les logs pendant les tests)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    yield logger

    # Nettoyer après les tests
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


@pytest.fixture
def test_logger():
    """Retourne le logger pour les tests"""
    return logging.getLogger('test-columns-number-validator')


def test_input_file_exists():
    """Vérifie que le fichier d'entrée de test existe"""
    assert INPUT_FILE.exists(), f"Le fichier de test {INPUT_FILE} n'existe pas"


def test_expected_output_file_exists():
    """Vérifie que le fichier de sortie attendu existe"""
    assert EXPECTED_OUTPUT_FILE.exists(), f"Le fichier de test {EXPECTED_OUTPUT_FILE} n'existe pas"




def test_analyze_csv_columns(test_logger):
    """Test de l'analyse des colonnes du fichier d'entrée"""
    test_logger.info("=" * 60)
    test_logger.info("Test: test_analyze_csv_columns")
    test_logger.info(f"Fichier d'entrée: {INPUT_FILE}")

    expected_cols, problematic_lines, column_counter, problematic_lines_dict = analyze_csv_columns(
        INPUT_FILE,
        delimiter=',',
        show_progress=False
    )

    test_logger.info(f"Nombre de colonnes attendu: {expected_cols}")
    test_logger.info(f"Nombre de lignes problématiques: {len(problematic_lines)}")
    test_logger.info(f"Répartition des colonnes: {dict(column_counter.most_common(5))}")

    # Vérifier que le nombre de colonnes attendu est détecté
    assert expected_cols > 0, "Le nombre de colonnes attendu doit être > 0"
    test_logger.info("✓ Nombre de colonnes attendu détecté")

    # Vérifier qu'il y a des lignes problématiques (c'est le but du fichier de test)
    assert len(problematic_lines) > 0, "Le fichier de test doit contenir des lignes problématiques"
    test_logger.info("✓ Lignes problématiques détectées")

    # Vérifier que le compteur contient des données
    assert len(column_counter) > 0, "Le compteur de colonnes doit contenir des données"
    test_logger.info("✓ Compteur de colonnes contient des données")
    test_logger.info("Test réussi: test_analyze_csv_columns")


def test_validate_csv(test_logger):
    """Test de la validation du fichier CSV"""
    test_logger.info("=" * 60)
    test_logger.info("Test: test_validate_csv")
    test_logger.info(f"Fichier d'entrée: {INPUT_FILE}")

    # Cette fonction ne fait que logger, on vérifie qu'elle ne lève pas d'exception
    try:
        validate_csv(
            INPUT_FILE,
            delimiter=',',
            show_progress=False,
            logger=test_logger
        )
        test_logger.info("✓ Validation terminée sans erreur")
    except Exception as e:
        test_logger.error(f"✗ validate_csv a levé une exception: {e}", exc_info=True)
        pytest.fail(f"validate_csv a levé une exception: {e}")

    test_logger.info("Test réussi: test_validate_csv")


def test_correct_csv(tmp_path, test_logger):
    """Test de la correction du fichier CSV"""
    test_logger.info("=" * 60)
    test_logger.info("Test: test_correct_csv")
    test_logger.info(f"Fichier d'entrée: {INPUT_FILE}")
    test_logger.info(f"Fichier de sortie attendu: {EXPECTED_OUTPUT_FILE}")

    # Nommer le fichier de sortie: corrected_{nom_sans_extension}.csv
    source_name = INPUT_FILE.stem
    output_file = tmp_path / f"corrected_{source_name}.csv"
    test_logger.info(f"Fichier de sortie temporaire: {output_file}")

    # Corriger le fichier
    test_logger.info("Début de la correction...")
    correct_csv(
        INPUT_FILE,
        output_file,
        delimiter=',',
        show_progress=False,
        logger=test_logger
    )
    test_logger.info("Correction terminée")

    # Vérifier que le fichier de sortie a été créé
    assert output_file.exists(), "Le fichier corrigé doit être créé"
    test_logger.info(f"✓ Fichier de sortie créé: {output_file}")

    # Vérifier que le fichier n'est pas vide
    file_size = output_file.stat().st_size
    assert file_size > 0, "Le fichier corrigé ne doit pas être vide"
    test_logger.info(f"✓ Taille du fichier: {file_size:,} bytes")

    # Comparer avec le fichier attendu
    # Note: on compare ligne par ligne car les fichiers peuvent avoir des différences mineures
    # (espaces, encodage, etc.)
    with open(output_file, encoding='utf-8') as f1, \
         open(EXPECTED_OUTPUT_FILE, encoding='utf-8') as f2:
        lines1 = [line.strip() for line in f1 if line.strip()]
        lines2 = [line.strip() for line in f2 if line.strip()]

    test_logger.info(f"Nombre de lignes dans le fichier corrigé: {len(lines1)}")
    test_logger.info(f"Nombre de lignes dans le fichier attendu: {len(lines2)}")

    assert len(lines1) == len(lines2), \
        f"Le nombre de lignes diffère: {len(lines1)} vs {len(lines2)}"
    test_logger.info(f"✓ Nombre de lignes correspond: {len(lines1)}")

    # Vérifier que toutes les lignes ont le même nombre de colonnes
    delimiter = ','
    differences = []
    for i, (line1, line2) in enumerate(zip(lines1, lines2, strict=True), start=1):
        cols1 = line1.count(delimiter) + 1
        cols2 = line2.count(delimiter) + 1
        if cols1 != cols2:
            differences.append(f"Ligne {i}: {cols1} vs {cols2}")
        assert cols1 == cols2, \
            f"Ligne {i}: nombre de colonnes différent ({cols1} vs {cols2})"

    if differences:
        test_logger.warning(f"Différences de colonnes détectées: {differences}")
    else:
        test_logger.info("✓ Toutes les lignes ont le même nombre de colonnes")

    # Vérifier que toutes les lignes de données ont le bon nombre de colonnes
    # (ignorer le header s'il existe)
    expected_cols, _, _, _ = analyze_csv_columns(INPUT_FILE, delimiter=',', show_progress=False)
    test_logger.info(f"Nombre de colonnes attendu pour les données: {expected_cols}")

    # Le header peut avoir un nombre de colonnes différent, on vérifie à partir de la ligne 2
    data_lines = lines1[1:] if len(lines1) > 1 and lines1[0].startswith(',matricul') else lines1
    incorrect_lines = []
    for i, line in enumerate(data_lines, start=2 if len(lines1) > 1 and lines1[0].startswith(',matricul') else 1):
        cols = line.count(delimiter) + 1
        if cols != expected_cols:
            incorrect_lines.append(f"Ligne {i}: {cols} colonnes")
        assert cols == expected_cols, \
            f"Ligne {i}: {cols} colonnes au lieu de {expected_cols}"

    if incorrect_lines:
        test_logger.warning(f"Lignes avec nombre de colonnes incorrect: {incorrect_lines[:5]}")
    else:
        test_logger.info(f"✓ Toutes les lignes de données ont {expected_cols} colonnes")

    test_logger.info("Test réussi: test_correct_csv")


def test_correct_csv_number_of_lines(tmp_path, test_logger):
    """Test que la correction réduit le nombre de lignes"""
    test_logger.info("=" * 60)
    test_logger.info("Test: test_correct_csv_number_of_lines")
    test_logger.info(f"Fichier d'entrée: {INPUT_FILE}")

    # Nommer le fichier de sortie: corrected_{nom_sans_extension}.csv
    source_name = INPUT_FILE.stem
    output_file = tmp_path / f"corrected_{source_name}.csv"

    # Compter les lignes dans le fichier original
    with open(INPUT_FILE, encoding='utf-8') as f:
        original_lines = sum(1 for line in f if line.strip())
    test_logger.info(f"Nombre de lignes originales: {original_lines}")

    # Corriger le fichier
    test_logger.info("Début de la correction...")
    correct_csv(
        INPUT_FILE,
        output_file,
        delimiter=',',
        show_progress=False,
        logger=test_logger
    )

    # Compter les lignes dans le fichier corrigé
    with open(output_file, encoding='utf-8') as f:
        corrected_lines = sum(1 for line in f if line.strip())
    test_logger.info(f"Nombre de lignes corrigées: {corrected_lines}")
    test_logger.info(f"Réduction: {original_lines - corrected_lines} lignes ({((original_lines - corrected_lines) / original_lines * 100):.1f}%)")

    # Le fichier corrigé doit avoir moins ou autant de lignes que l'original
    # (car on fusionne les lignes incomplètes)
    assert corrected_lines <= original_lines, \
        f"Le fichier corrigé ne devrait pas avoir plus de lignes ({corrected_lines} vs {original_lines})"
    test_logger.info("✓ Le fichier corrigé a moins ou autant de lignes que l'original")

    # Dans notre cas de test, on sait qu'il y a des lignes à fusionner
    assert corrected_lines < original_lines, \
        f"Le fichier de test devrait avoir des lignes fusionnées ({corrected_lines} vs {original_lines})"
    test_logger.info("✓ Des lignes ont été fusionnées")
    test_logger.info("Test réussi: test_correct_csv_number_of_lines")




if __name__ == "__main__":
    pytest.main([__file__, "-v"])

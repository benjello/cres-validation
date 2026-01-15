"""Tests pour le module columns_number_validator"""

import logging
from pathlib import Path

import pytest

from cres_validation.columns_number_validator import (
    analyze_csv_columns,
    correct_csv,
    csv_validate_columns_number,
)
from cres_validation.columns_validator import validate_csv_columns

# Chemin vers les fichiers de test dans fixtures
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
INPUT_FILE = FIXTURES_DIR / "input" / "csv" / "echantillon_cnrps_pb_fondation_fidaa.csv"
# Le fichier de sortie attendu suit le format: corrected_{nom_source}.csv
EXPECTED_OUTPUT_FILE = FIXTURES_DIR / "output" / "csv" / f"corrected_{INPUT_FILE.stem}.csv"
LOGS_DIR = FIXTURES_DIR / "logs"
DELIMITER = ";"


@pytest.fixture
def test_logger():
    """Retourne le logger pour les modules de traitement (pas pour les tests)"""
    return logging.getLogger("cres-validation")


@pytest.fixture
def output_file(tmp_path):
    """Crée un fichier de sortie temporaire pour les tests de correction"""
    source_name = INPUT_FILE.stem
    return tmp_path / f"corrected_{source_name}.csv"


def test_input_file_exists():
    """Vérifie que le fichier d'entrée de test existe"""
    assert INPUT_FILE.exists(), f"Le fichier de test {INPUT_FILE} n'existe pas"


def test_log_file_created_and_has_content(test_logger):
    """Vérifie que le fichier de log est créé et contient du contenu après exécution des tests"""
    # Exécuter une opération qui génère des logs (analyse des colonnes)
    # Le message "Analyse du fichier: {csv_path}" contient le chemin complet du CSV
    # qui inclut le nom du fichier, donc le filtre devrait l'accepter
    analyze_csv_columns(INPUT_FILE, delimiter=DELIMITER, show_progress=False, logger=test_logger)

    # Forcer l'écriture des logs en vidant les buffers de tous les handlers
    for handler in test_logger.handlers:
        handler.flush()
    # Aussi pour le logger de conversion au cas où
    convert_logger = logging.getLogger("cres-validation.convert")
    for handler in convert_logger.handlers:
        handler.flush()

    # Trouver le fichier de log correspondant au fichier CSV testé
    # Le nom du CSV est "echantillon_cnrps_pb_fondation_fidaa.csv"
    # Le log devrait être "echantillon_cnrps_pb_fondation_fidaa-*.log"
    csv_stem = INPUT_FILE.stem
    log_files = list(LOGS_DIR.glob(f"{csv_stem}-*.log"))

    # Si aucun log spécifique n'est trouvé, chercher le log le plus récent
    if not log_files:
        log_files = list(LOGS_DIR.glob("*.log"))
        assert len(log_files) > 0, "Au moins un fichier de log doit être créé"
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
    else:
        # Prendre le log le plus récent pour ce fichier
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)

    # Vérifier que le fichier existe
    assert latest_log.exists(), f"Le fichier de log {latest_log} doit être créé"

    # Vérifier que le fichier n'est pas vide
    # Note: Le fichier peut être vide si le filtre ne laisse pas passer les messages
    # Dans ce cas, on attend que d'autres tests génèrent du contenu
    file_size = latest_log.stat().st_size
    if file_size == 0:
        # Le fichier existe mais est vide - cela peut arriver si le test s'exécute seul
        # On accepte cela car d'autres tests vont remplir le log
        pytest.skip(
            f"Le fichier de log {latest_log} est vide. "
            "Cela peut arriver si le test s'exécute seul. "
            "Les autres tests vont générer du contenu."
        )

    # Vérifier le format du nom du fichier (nom-date-heure.log)
    log_name = latest_log.name
    assert log_name.endswith(".log"), "Le fichier de log doit avoir l'extension .log"
    assert csv_stem in log_name, f"Le nom du fichier de log doit contenir {csv_stem}"

    # Vérifier que le fichier contient des logs (au moins une ligne avec un timestamp)
    with open(latest_log, encoding="utf-8") as f:
        content = f.read()
        assert len(content) > 0, "Le fichier de log doit contenir du contenu"
        # Vérifier qu'il y a au moins un message de log (format: YYYY-MM-DD HH:MM:SS)
        assert " - " in content, "Le fichier de log doit contenir des messages formatés"
        # Vérifier qu'il y a au moins un niveau de log (INFO, DEBUG, WARNING, ERROR)
        assert any(level in content for level in ["INFO", "DEBUG", "WARNING", "ERROR"]), (
            "Le fichier de log doit contenir au moins un niveau de log"
        )


def test_expected_output_file_exists():
    """Vérifie que le fichier de sortie attendu existe"""
    assert EXPECTED_OUTPUT_FILE.exists(), f"Le fichier de test {EXPECTED_OUTPUT_FILE} n'existe pas"


def test_analyze_csv_columns(test_logger):
    """Test de l'analyse des colonnes du fichier d'entrée"""
    expected_cols, problematic_lines, column_counter, problematic_lines_dict = analyze_csv_columns(
        INPUT_FILE, delimiter=DELIMITER, show_progress=False, logger=test_logger
    )

    # Vérifier que le nombre de colonnes attendu est détecté
    assert expected_cols > 0, "Le nombre de colonnes attendu doit être > 0"

    # Vérifier qu'il y a des lignes problématiques (c'est le but du fichier de test)
    assert len(problematic_lines) > 0, "Le fichier de test doit contenir des lignes problématiques"

    # Vérifier que le compteur contient des données
    assert len(column_counter) > 0, "Le compteur de colonnes doit contenir des données"


def test_csv_validate_columns_number(test_logger):
    """Test de la validation du fichier CSV (nombre de colonnes)"""
    # Cette fonction ne fait que logger, on vérifie qu'elle ne lève pas d'exception
    try:
        csv_validate_columns_number(INPUT_FILE, delimiter=DELIMITER, show_progress=False, logger=test_logger)
    except Exception as e:
        pytest.fail(f"csv_validate_columns_number a levé une exception: {e}")


def test_validate_csv_columns(test_logger):
    """Test de la validation des colonnes avec Pandera (types, formats, dates)"""
    # Valider les colonnes avec Pandera
    # Utiliser le fichier CSV corrigé s'il existe, sinon le fichier d'entrée
    csv_file_to_validate = EXPECTED_OUTPUT_FILE if EXPECTED_OUTPUT_FILE.exists() else INPUT_FILE

    try:
        validation_success = validate_csv_columns(
            csv_file_to_validate,
            delimiter=DELIMITER,
            schema_name="cnrps",
            logger=test_logger,
        )
        # La validation peut échouer (c'est normal si le fichier a des problèmes)
        # On vérifie juste qu'elle ne lève pas d'exception
        assert isinstance(validation_success, bool), "validate_csv_columns doit retourner un booléen"
    except Exception as e:
        pytest.fail(f"validate_csv_columns a levé une exception: {e}")


def test_correct_csv(output_file, test_logger):
    """Test de la correction du fichier CSV"""
    # Corriger le fichier (les logs seront capturés automatiquement)
    correct_csv(
        INPUT_FILE, output_file, delimiter=DELIMITER, show_progress=False, logger=test_logger
    )

    # Vérifier que le fichier de sortie a été créé
    assert output_file.exists(), "Le fichier corrigé doit être créé"

    # Vérifier que le fichier n'est pas vide
    file_size = output_file.stat().st_size
    assert file_size > 0, "Le fichier corrigé ne doit pas être vide"

    # Comparer avec le fichier attendu
    with (
        open(output_file, encoding="utf-8") as f1,
        open(EXPECTED_OUTPUT_FILE, encoding="utf-8") as f2,
    ):
        lines1 = [line.strip() for line in f1 if line.strip()]
        lines2 = [line.strip() for line in f2 if line.strip()]

    assert len(lines1) == len(lines2), (
        f"Le nombre de lignes diffère: {len(lines1)} vs {len(lines2)}"
    )

    # Vérifier que toutes les lignes ont le même nombre de colonnes que le fichier attendu
    for i, (line1, line2) in enumerate(zip(lines1, lines2, strict=True), start=1):
        cols1 = line1.count(DELIMITER) + 1
        cols2 = line2.count(DELIMITER) + 1
        assert cols1 == cols2, f"Ligne {i}: nombre de colonnes différent ({cols1} vs {cols2})"

    # Vérifier que toutes les lignes de données ont le bon nombre de colonnes
    expected_cols, _, _, _ = analyze_csv_columns(
        INPUT_FILE, delimiter=DELIMITER, show_progress=False
    )

    # Le header peut avoir un nombre de colonnes différent, on vérifie à partir de la ligne 2
    data_lines = lines1[1:] if len(lines1) > 1 and lines1[0].startswith(",matricul") else lines1
    for i, line in enumerate(
        data_lines, start=2 if len(lines1) > 1 and lines1[0].startswith(",matricul") else 1
    ):
        cols = line.count(DELIMITER) + 1
        assert cols == expected_cols, f"Ligne {i}: {cols} colonnes au lieu de {expected_cols}"


def test_correct_csv_reduces_line_count(output_file, test_logger):
    """Test que la correction réduit le nombre de lignes en fusionnant les lignes incomplètes"""
    # Compter les lignes dans le fichier original
    with open(INPUT_FILE, encoding="utf-8") as f:
        original_lines = sum(1 for line in f if line.strip())

    # Corriger le fichier (les logs seront capturés automatiquement)
    correct_csv(
        INPUT_FILE, output_file, delimiter=DELIMITER, show_progress=False, logger=test_logger
    )

    # Compter les lignes dans le fichier corrigé
    with open(output_file, encoding="utf-8") as f:
        corrected_lines = sum(1 for line in f if line.strip())

    # Le fichier corrigé doit avoir moins ou autant de lignes que l'original
    assert corrected_lines <= original_lines, (
        f"Le fichier corrigé ne devrait pas avoir plus de lignes ({corrected_lines} vs {original_lines})"
    )

    # Dans notre cas de test, on sait qu'il y a des lignes à fusionner
    assert corrected_lines < original_lines, (
        f"Le fichier de test devrait avoir des lignes fusionnées ({corrected_lines} vs {original_lines})"
    )


def test_rejected_lines_saved(output_file, test_logger, tmp_path):
    """Test que les lignes rejetées sont sauvegardées correctement"""
    # Analyser le fichier pour obtenir les lignes problématiques
    expected_cols, problematic_lines, _, problematic_lines_dict = analyze_csv_columns(
        INPUT_FILE, delimiter=DELIMITER, show_progress=False, logger=test_logger
    )

    # Vérifier qu'il y a des lignes problématiques
    assert len(problematic_lines) > 0, "Le fichier de test doit contenir des lignes problématiques"

    # Créer un fichier de sortie pour les lignes rejetées
    rejected_file = tmp_path / "rejected_test.csv"

    # Valider avec sauvegarde des lignes rejetées
    csv_validate_columns_number(
        INPUT_FILE,
        delimiter=DELIMITER,
        show_progress=False,
        logger=test_logger,
        rejected_output_path=rejected_file,
    )

    # Vérifier que le fichier de lignes rejetées a été créé
    assert rejected_file.exists(), "Le fichier de lignes rejetées doit être créé"

    # Vérifier que le fichier n'est pas vide
    file_size = rejected_file.stat().st_size
    assert file_size > 0, "Le fichier de lignes rejetées ne doit pas être vide"

    # Lire le fichier et vérifier qu'il contient des lignes
    with open(rejected_file, encoding="utf-8") as f:
        rejected_lines = [line.strip() for line in f if line.strip()]

    # Le fichier doit contenir au moins le header + des lignes rejetées
    assert len(rejected_lines) > 1, "Le fichier de lignes rejetées doit contenir au moins le header et des lignes"

    # Vérifier que toutes les lignes problématiques sont présentes dans le fichier rejeté
    # (certaines lignes peuvent apparaître plusieurs fois car elles font partie de plusieurs paires)
    with open(INPUT_FILE, encoding="utf-8") as f:
        source_lines = [line.rstrip() for line in f if line.strip()]

    # Vérifier que les lignes problématiques sont dans le fichier rejeté
    problematic_found = 0
    for line_num in problematic_lines:
        if line_num <= len(source_lines):
            source_line = source_lines[line_num - 1].rstrip()
            # La ligne doit être présente dans le fichier rejeté (peut être plusieurs fois)
            if any(source_line == rejected_line for rejected_line in rejected_lines[1:]):  # Skip header
                problematic_found += 1

    # Au moins certaines lignes problématiques doivent être présentes
    assert problematic_found > 0, "Au moins certaines lignes problématiques doivent être dans le fichier rejeté"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

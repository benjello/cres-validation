"""Tests de performance pour mesurer le temps d'exécution"""

import logging
import time
from pathlib import Path

import pytest

from cres_validation.columns_number_validator import analyze_csv_columns, correct_csv
from cres_validation.convert_txt_to_csv import convert_txt_to_csv

# Chemin vers les fichiers de test dans fixtures
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
SOURCE_DIR = FIXTURES_DIR / "input" / "source"
CSV_DIR = FIXTURES_DIR / "input" / "csv"
OUTPUT_DIR = FIXTURES_DIR / "output"
LOGS_DIR = FIXTURES_DIR / "logs"

# Fichier source original (petit, stocké dans le repo)
SOURCE_FILE = SOURCE_DIR / "echantillon cnrps pb fondation fidaa.txt"

DELIMITER = ","


@pytest.fixture
def performance_logger():
    """Logger pour les tests de performance"""
    logger = logging.getLogger("cres-validation.performance")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def format_time(seconds: float) -> str:
    """Formate le temps en unité appropriée"""
    if seconds < 1:
        return f"{seconds * 1000:.2f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"


def generate_test_file(num_lines: int, output_path: Path, source_file: Path = SOURCE_FILE) -> None:
    """
    Génère un fichier de test avec le nombre de lignes spécifié.

    Args:
        num_lines: Nombre de lignes de données (hors header)
        output_path: Chemin du fichier de sortie
        source_file: Fichier source pour extraire le header et les données
    """
    if not source_file.exists():
        raise FileNotFoundError(f"Fichier source non trouvé: {source_file}")

    # Lire le fichier source
    with open(source_file, encoding="utf-8") as f:
        lines = [line.rstrip("\n\r") for line in f if line.strip()]

    if not lines:
        raise ValueError("Le fichier source est vide")

    header = lines[0]
    data_lines = lines[1:]  # Toutes les lignes sauf le header

    if not data_lines:
        raise ValueError("Le fichier source n'a pas de lignes de données")

    # Générer le fichier de test
    with open(output_path, "w", encoding="utf-8", buffering=8192 * 16) as f:
        f.write(header + "\n")
        # Dupliquer les lignes existantes pour atteindre le nombre de lignes souhaité
        for i in range(num_lines):
            if (i + 1) % 100_000 == 0 and num_lines >= 100_000:
                print(f"  Génération: {(i + 1) // 1000}k lignes...")
            f.write(data_lines[i % len(data_lines)] + "\n")


def test_performance_convert_1k(performance_logger, tmp_path):
    """Test de performance : conversion TXT vers CSV pour 1000 lignes"""
    if not SOURCE_FILE.exists():
        pytest.skip(f"Fichier source non trouvé: {SOURCE_FILE}")

    # Générer le fichier de test à la volée
    test_file = tmp_path / "test_1k.txt"
    print("📝 Génération du fichier de test (1k lignes)...")
    generate_test_file(1000, test_file)

    # Créer un répertoire source temporaire avec le fichier généré
    test_source_dir = tmp_path / "source_1k"
    test_source_dir.mkdir()
    test_file_in_dir = test_source_dir / test_file.name
    test_file.rename(test_file_in_dir)

    output_dir = tmp_path / "csv_1k"
    output_dir.mkdir()

    start_time = time.time()

    convert_txt_to_csv(test_source_dir, output_dir, logger=performance_logger)

    elapsed = time.time() - start_time

    # Vérifier que le fichier a été créé
    csv_file = output_dir / (test_file_in_dir.stem.replace(" ", "_") + ".csv")
    assert csv_file.exists(), "Le fichier CSV doit être créé"

    # Compter les lignes
    with open(csv_file, encoding="utf-8") as f:
        line_count = sum(1 for line in f if line.strip())

    print("\n⏱️  Performance conversion 1k lignes:")
    print(f"   - Temps: {format_time(elapsed)}")
    print(f"   - Lignes traitées: {line_count:,}")
    print(f"   - Vitesse: {line_count / elapsed:,.0f} lignes/seconde")

    assert elapsed < 10, (
        f"La conversion devrait prendre moins de 10 secondes, mais a pris {elapsed:.2f}s"
    )


def test_performance_analyze_1k(performance_logger, tmp_path):
    """Test de performance : analyse CSV pour 1000 lignes"""
    if not SOURCE_FILE.exists():
        pytest.skip(f"Fichier source non trouvé: {SOURCE_FILE}")

    # Générer le fichier de test à la volée
    test_file = tmp_path / "test_1k.txt"
    print("📝 Génération du fichier de test (1k lignes)...")
    generate_test_file(1000, test_file)

    # Créer un répertoire source temporaire avec le fichier généré
    test_source_dir = tmp_path / "source_1k"
    test_source_dir.mkdir()
    test_file_in_dir = test_source_dir / test_file.name
    test_file.rename(test_file_in_dir)

    # Convertir d'abord
    output_dir = tmp_path / "csv_1k"
    output_dir.mkdir()
    convert_txt_to_csv(test_source_dir, output_dir, logger=performance_logger)
    csv_file = output_dir / (test_file_in_dir.stem.replace(" ", "_") + ".csv")

    start_time = time.time()

    expected_cols, problematic_lines, column_counter, _ = analyze_csv_columns(
        csv_file, delimiter=DELIMITER, show_progress=False, logger=performance_logger
    )

    elapsed = time.time() - start_time

    total_lines = sum(column_counter.values())

    print("\n⏱️  Performance analyse 1k lignes:")
    print(f"   - Temps: {format_time(elapsed)}")
    print(f"   - Lignes analysées: {total_lines:,}")
    print(f"   - Lignes problématiques: {len(problematic_lines):,}")
    print(f"   - Vitesse: {total_lines / elapsed:,.0f} lignes/seconde")

    assert elapsed < 5, f"L'analyse devrait prendre moins de 5 secondes, mais a pris {elapsed:.2f}s"


def test_performance_correct_1k(performance_logger, tmp_path):
    """Test de performance : correction CSV pour 1000 lignes"""
    if not SOURCE_FILE.exists():
        pytest.skip(f"Fichier source non trouvé: {SOURCE_FILE}")

    # Générer le fichier de test à la volée
    test_file = tmp_path / "test_1k.txt"
    print("📝 Génération du fichier de test (1k lignes)...")
    generate_test_file(1000, test_file)

    # Créer un répertoire source temporaire avec le fichier généré
    test_source_dir = tmp_path / "source_1k"
    test_source_dir.mkdir()
    test_file_in_dir = test_source_dir / test_file.name
    test_file.rename(test_file_in_dir)

    # Convertir d'abord
    output_dir = tmp_path / "csv_1k"
    output_dir.mkdir()
    convert_txt_to_csv(test_source_dir, output_dir, logger=performance_logger)
    csv_file = output_dir / (test_file_in_dir.stem.replace(" ", "_") + ".csv")

    corrected_file = tmp_path / "corrected_1k.csv"

    start_time = time.time()

    correct_csv(
        csv_file,
        corrected_file,
        delimiter=DELIMITER,
        show_progress=False,
        logger=performance_logger,
    )

    elapsed = time.time() - start_time

    # Compter les lignes dans le fichier corrigé
    with open(corrected_file, encoding="utf-8") as f:
        corrected_lines = sum(1 for line in f if line.strip())

    print("\n⏱️  Performance correction 1k lignes:")
    print(f"   - Temps: {format_time(elapsed)}")
    print(f"   - Lignes corrigées: {corrected_lines:,}")
    print(f"   - Vitesse: {corrected_lines / elapsed:,.0f} lignes/seconde")

    assert elapsed < 10, (
        f"La correction devrait prendre moins de 10 secondes, mais a pris {elapsed:.2f}s"
    )


@pytest.mark.slow
def test_performance_convert_1m(performance_logger, tmp_path):
    """Test de performance : conversion TXT vers CSV pour 1 million de lignes"""
    if not SOURCE_FILE.exists():
        pytest.skip(f"Fichier source non trouvé: {SOURCE_FILE}")

    # Générer le fichier de test à la volée
    test_file = tmp_path / "test_1m.txt"
    print("📝 Génération du fichier de test (1M lignes)...")
    print("   (Cela peut prendre quelques instants...)")
    generate_test_file(1_000_000, test_file)

    # Créer un répertoire source temporaire avec le fichier généré
    test_source_dir = tmp_path / "source_1m"
    test_source_dir.mkdir()
    test_file_in_dir = test_source_dir / test_file.name
    # Copier le fichier au lieu de le renommer (car test_file est un Path)
    import shutil

    shutil.copy2(test_file, test_file_in_dir)

    output_dir = tmp_path / "csv_1m"
    output_dir.mkdir()

    start_time = time.time()

    convert_txt_to_csv(test_source_dir, output_dir, logger=performance_logger)

    elapsed = time.time() - start_time

    # Vérifier que le fichier a été créé
    csv_file = output_dir / (test_file_in_dir.stem.replace(" ", "_") + ".csv")
    assert csv_file.exists(), "Le fichier CSV doit être créé"

    # Compter les lignes (rapide avec wc si disponible, sinon compter)
    with open(csv_file, encoding="utf-8") as f:
        line_count = sum(1 for line in f if line.strip())

    print("\n⏱️  Performance conversion 1M lignes:")
    print(f"   - Temps: {format_time(elapsed)}")
    print(f"   - Lignes traitées: {line_count:,}")
    print(f"   - Vitesse: {line_count / elapsed:,.0f} lignes/seconde")

    # Pour 1M lignes, on accepte jusqu'à 5 minutes
    assert elapsed < 300, (
        f"La conversion devrait prendre moins de 5 minutes, mais a pris {format_time(elapsed)}"
    )


@pytest.mark.slow
def test_performance_analyze_1m(performance_logger, tmp_path):
    """Test de performance : analyse CSV pour 1 million de lignes"""
    if not SOURCE_FILE.exists():
        pytest.skip(f"Fichier source non trouvé: {SOURCE_FILE}")

    # Générer le fichier de test à la volée
    test_file = tmp_path / "test_1m.txt"
    print("📝 Génération du fichier de test (1M lignes)...")
    print("   (Cela peut prendre quelques instants...)")
    generate_test_file(1_000_000, test_file)

    # Créer un répertoire source temporaire avec le fichier généré
    test_source_dir = tmp_path / "source_1m"
    test_source_dir.mkdir()
    test_file_in_dir = test_source_dir / test_file.name
    # Copier le fichier au lieu de le renommer (car test_file est un Path)
    import shutil

    shutil.copy2(test_file, test_file_in_dir)

    # Convertir d'abord
    output_dir = tmp_path / "csv_1m"
    output_dir.mkdir()
    convert_txt_to_csv(test_source_dir, output_dir, logger=performance_logger)
    csv_file = output_dir / (test_file_in_dir.stem.replace(" ", "_") + ".csv")

    start_time = time.time()

    expected_cols, problematic_lines, column_counter, _ = analyze_csv_columns(
        csv_file, delimiter=DELIMITER, show_progress=True, logger=performance_logger
    )

    elapsed = time.time() - start_time

    total_lines = sum(column_counter.values())

    print("\n⏱️  Performance analyse 1M lignes:")
    print(f"   - Temps: {format_time(elapsed)}")
    print(f"   - Lignes analysées: {total_lines:,}")
    print(f"   - Lignes problématiques: {len(problematic_lines):,}")
    print(f"   - Vitesse: {total_lines / elapsed:,.0f} lignes/seconde")

    # Pour 1M lignes, on accepte jusqu'à 2 minutes
    assert elapsed < 120, (
        f"L'analyse devrait prendre moins de 2 minutes, mais a pris {format_time(elapsed)}"
    )


@pytest.mark.slow
def test_performance_correct_1m(performance_logger, tmp_path):
    """Test de performance : correction CSV pour 1 million de lignes"""
    if not SOURCE_FILE.exists():
        pytest.skip(f"Fichier source non trouvé: {SOURCE_FILE}")

    # Générer le fichier de test à la volée
    test_file = tmp_path / "test_1m.txt"
    print("📝 Génération du fichier de test (1M lignes)...")
    print("   (Cela peut prendre quelques instants...)")
    generate_test_file(1_000_000, test_file)

    # Créer un répertoire source temporaire avec le fichier généré
    test_source_dir = tmp_path / "source_1m"
    test_source_dir.mkdir()
    test_file_in_dir = test_source_dir / test_file.name
    # Copier le fichier au lieu de le renommer (car test_file est un Path)
    import shutil

    shutil.copy2(test_file, test_file_in_dir)

    # Convertir d'abord
    output_dir = tmp_path / "csv_1m"
    output_dir.mkdir()
    convert_txt_to_csv(test_source_dir, output_dir, logger=performance_logger)
    csv_file = output_dir / (test_file_in_dir.stem.replace(" ", "_") + ".csv")

    corrected_file = tmp_path / "corrected_1m.csv"

    start_time = time.time()

    correct_csv(
        csv_file, corrected_file, delimiter=DELIMITER, show_progress=True, logger=performance_logger
    )

    elapsed = time.time() - start_time

    # Compter les lignes dans le fichier corrigé
    with open(corrected_file, encoding="utf-8") as f:
        corrected_lines = sum(1 for line in f if line.strip())

    print("\n⏱️  Performance correction 1M lignes:")
    print(f"   - Temps: {format_time(elapsed)}")
    print(f"   - Lignes corrigées: {corrected_lines:,}")
    print(f"   - Vitesse: {corrected_lines / elapsed:,.0f} lignes/seconde")

    # Pour 1M lignes, on accepte jusqu'à 5 minutes
    assert elapsed < 300, (
        f"La correction devrait prendre moins de 5 minutes, mais a pris {format_time(elapsed)}"
    )

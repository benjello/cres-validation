"""Tests pour la conversion CSV vers Parquet"""

import logging
from pathlib import Path

import pandas as pd
import pytest

from cres_validation.convert_to_parquet import convert_csv_to_parquet

# Chemin vers les fichiers de test dans fixtures
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
CSV_DIR = FIXTURES_DIR / "output" / "csv"
PARQUET_DIR = FIXTURES_DIR / "output" / "parquet"
DELIMITER = ";"


@pytest.fixture
def test_logger():
    """Crée un logger pour les tests"""
    logger = logging.getLogger("test-parquet")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def test_csv_to_parquet_conversion(test_logger, tmp_path):
    """Test de conversion CSV vers Parquet"""
    # Utiliser un fichier CSV de test
    csv_file = CSV_DIR / "corrected_echantillon_cnrps_pb_fondation_fidaa.csv"

    if not csv_file.exists():
        pytest.skip(f"Fichier CSV de test introuvable: {csv_file}")

    # Chemin pour le fichier Parquet de test
    parquet_file = tmp_path / "test_output.parquet"

    # Convertir
    convert_csv_to_parquet(csv_file, parquet_file, delimiter=DELIMITER, logger=test_logger)

    # Vérifier que le fichier Parquet existe
    assert parquet_file.exists(), "Le fichier Parquet n'a pas été créé"

    # Vérifier que le fichier n'est pas vide
    assert parquet_file.stat().st_size > 0, "Le fichier Parquet est vide"


def test_csv_parquet_data_conformity(test_logger, tmp_path):
    """Test de conformité des données entre CSV et Parquet"""
    # Utiliser un fichier CSV de test
    csv_file = CSV_DIR / "corrected_echantillon_cnrps_pb_fondation_fidaa.csv"

    if not csv_file.exists():
        pytest.skip(f"Fichier CSV de test introuvable: {csv_file}")

    # Lire le CSV original
    df_csv = pd.read_csv(csv_file, delimiter=DELIMITER, dtype=str, keep_default_na=False)

    # Convertir en Parquet
    parquet_file = tmp_path / "test_conformity.parquet"
    convert_csv_to_parquet(csv_file, parquet_file, delimiter=DELIMITER, logger=test_logger)

    # Lire le Parquet
    df_parquet = pd.read_parquet(parquet_file)

    # Vérifier que les DataFrames ont les mêmes dimensions
    assert df_csv.shape == df_parquet.shape, (
        f"Dimensions différentes: CSV {df_csv.shape} vs Parquet {df_parquet.shape}"
    )

    # Vérifier que les colonnes sont identiques
    assert list(df_csv.columns) == list(df_parquet.columns), (
        f"Colonnes différentes: CSV {list(df_csv.columns)} vs Parquet {list(df_parquet.columns)}"
    )

    # Vérifier que les données sont identiques
    # Convertir les deux DataFrames en string pour la comparaison (pour gérer les types)
    # Remplacer NaN par chaîne vide pour la comparaison
    df_csv_str = df_csv.fillna("").astype(str)
    df_parquet_str = df_parquet.fillna("").astype(str)

    # Réindexer pour s'assurer que les index sont identiques
    df_csv_str = df_csv_str.reset_index(drop=True)
    df_parquet_str = df_parquet_str.reset_index(drop=True)

    # Comparer ligne par ligne
    pd.testing.assert_frame_equal(
        df_csv_str,
        df_parquet_str,
        check_names=True,
        check_dtype=False,  # On compare les valeurs, pas les types
    )


def test_csv_parquet_all_files_conformity(test_logger, tmp_path):
    """Test de conformité pour tous les fichiers CSV corrigés"""
    # Trouver tous les fichiers CSV corrigés
    csv_files = list(CSV_DIR.glob("corrected_*.csv"))

    if not csv_files:
        pytest.skip("Aucun fichier CSV corrigé trouvé pour les tests")

    for csv_file in csv_files:
        # Lire le CSV original
        df_csv = pd.read_csv(csv_file, delimiter=DELIMITER, dtype=str, keep_default_na=False)

        # Convertir en Parquet
        parquet_file = tmp_path / f"{csv_file.stem}.parquet"
        convert_csv_to_parquet(csv_file, parquet_file, delimiter=DELIMITER, logger=test_logger)

        # Lire le Parquet
        df_parquet = pd.read_parquet(parquet_file)

        # Vérifier les dimensions
        assert df_csv.shape == df_parquet.shape, (
            f"Fichier {csv_file.name}: dimensions différentes "
            f"CSV {df_csv.shape} vs Parquet {df_parquet.shape}"
        )

        # Vérifier les colonnes
        assert list(df_csv.columns) == list(df_parquet.columns), (
            f"Fichier {csv_file.name}: colonnes différentes"
        )

        # Vérifier les données (comparaison des valeurs en string)
        # Remplacer NaN par chaîne vide pour la comparaison
        df_csv_str = df_csv.fillna("").astype(str)
        df_parquet_str = df_parquet.fillna("").astype(str)

        # Réindexer pour s'assurer que les index sont identiques
        df_csv_str = df_csv_str.reset_index(drop=True)
        df_parquet_str = df_parquet_str.reset_index(drop=True)

        pd.testing.assert_frame_equal(
            df_csv_str,
            df_parquet_str,
            check_names=True,
            check_dtype=False,
        )


def test_parquet_file_exists_in_output():
    """Vérifie que les fichiers Parquet existent dans le répertoire output/parquet"""
    parquet_files = list(PARQUET_DIR.glob("corrected_*.parquet"))

    if not parquet_files:
        pytest.skip("Aucun fichier Parquet trouvé dans output/parquet")

    # Vérifier que chaque fichier Parquet a un CSV correspondant
    for parquet_file in parquet_files:
        # Extraire le nom du fichier source (sans l'extension .parquet)
        csv_name = parquet_file.stem + ".csv"
        csv_file = CSV_DIR / csv_name

        assert csv_file.exists(), (
            f"Fichier CSV correspondant introuvable pour {parquet_file.name}: {csv_file}"
        )

        # Vérifier que le fichier Parquet n'est pas vide
        assert parquet_file.stat().st_size > 0, f"Le fichier Parquet {parquet_file.name} est vide"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests pour le module csv_validator"""
from pathlib import Path

import pandas as pd
import pytest

from csv_validator import analyze_csv_columns, correct_csv, validate_csv

# Chemin vers les fichiers de test
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
INPUT_FILE = FIXTURES_DIR / "input.csv"
EXPECTED_OUTPUT_FILE = FIXTURES_DIR / "expected_output.csv"


def test_input_file_exists():
    """Vérifie que le fichier d'entrée de test existe"""
    assert INPUT_FILE.exists(), f"Le fichier de test {INPUT_FILE} n'existe pas"


def test_expected_output_file_exists():
    """Vérifie que le fichier de sortie attendu existe"""
    assert EXPECTED_OUTPUT_FILE.exists(), f"Le fichier de test {EXPECTED_OUTPUT_FILE} n'existe pas"


def test_analyze_csv_columns():
    """Test de l'analyse des colonnes du fichier d'entrée"""
    expected_cols, problematic_lines, column_counter, problematic_lines_dict = analyze_csv_columns(
        INPUT_FILE,
        delimiter=';',
        show_progress=False
    )

    # Vérifier que le nombre de colonnes attendu est détecté
    assert expected_cols > 0, "Le nombre de colonnes attendu doit être > 0"

    # Vérifier qu'il y a des lignes problématiques (c'est le but du fichier de test)
    assert len(problematic_lines) > 0, "Le fichier de test doit contenir des lignes problématiques"

    # Vérifier que le compteur contient des données
    assert len(column_counter) > 0, "Le compteur de colonnes doit contenir des données"


def test_validate_csv():
    """Test de la validation du fichier CSV"""
    # Cette fonction ne fait que logger, on vérifie qu'elle ne lève pas d'exception
    try:
        validate_csv(
            INPUT_FILE,
            delimiter=';',
            show_progress=False
        )
    except Exception as e:
        pytest.fail(f"validate_csv a levé une exception: {e}")


def test_correct_csv(tmp_path):
    """Test de la correction du fichier CSV"""
    output_file = tmp_path / "corrected_output.csv"

    # Corriger le fichier
    correct_csv(
        INPUT_FILE,
        output_file,
        delimiter=';',
        show_progress=False
    )

    # Vérifier que le fichier de sortie a été créé
    assert output_file.exists(), "Le fichier corrigé doit être créé"

    # Vérifier que le fichier n'est pas vide
    assert output_file.stat().st_size > 0, "Le fichier corrigé ne doit pas être vide"

    # Comparer avec le fichier attendu
    # Note: on compare ligne par ligne car les fichiers peuvent avoir des différences mineures
    # (espaces, encodage, etc.)
    with open(output_file, encoding='utf-8') as f1, \
         open(EXPECTED_OUTPUT_FILE, encoding='utf-8') as f2:
        lines1 = [line.strip() for line in f1 if line.strip()]
        lines2 = [line.strip() for line in f2 if line.strip()]

    assert len(lines1) == len(lines2), \
        f"Le nombre de lignes diffère: {len(lines1)} vs {len(lines2)}"

    # Vérifier que toutes les lignes ont le même nombre de colonnes
    delimiter = ';'
    for i, (line1, line2) in enumerate(zip(lines1, lines2, strict=True), start=1):
        cols1 = line1.count(delimiter) + 1
        cols2 = line2.count(delimiter) + 1
        assert cols1 == cols2, \
            f"Ligne {i}: nombre de colonnes différent ({cols1} vs {cols2})"

    # Vérifier que toutes les lignes ont le bon nombre de colonnes (58)
    expected_cols = 58
    for i, line in enumerate(lines1, start=1):
        cols = line.count(delimiter) + 1
        assert cols == expected_cols, \
            f"Ligne {i}: {cols} colonnes au lieu de {expected_cols}"


def test_correct_csv_number_of_lines(tmp_path):
    """Test que la correction réduit le nombre de lignes"""
    output_file = tmp_path / "corrected_output.csv"

    # Compter les lignes dans le fichier original
    with open(INPUT_FILE, encoding='utf-8') as f:
        original_lines = sum(1 for line in f if line.strip())

    # Corriger le fichier
    correct_csv(
        INPUT_FILE,
        output_file,
        delimiter=';',
        show_progress=False
    )

    # Compter les lignes dans le fichier corrigé
    with open(output_file, encoding='utf-8') as f:
        corrected_lines = sum(1 for line in f if line.strip())

    # Le fichier corrigé doit avoir moins ou autant de lignes que l'original
    # (car on fusionne les lignes incomplètes)
    assert corrected_lines <= original_lines, \
        f"Le fichier corrigé ne devrait pas avoir plus de lignes ({corrected_lines} vs {original_lines})"

    # Dans notre cas de test, on sait qu'il y a des lignes à fusionner
    assert corrected_lines < original_lines, \
        f"Le fichier de test devrait avoir des lignes fusionnées ({corrected_lines} vs {original_lines})"


def test_validate_columns_with_pandera(tmp_path):
    """Test de validation des colonnes avec Pandera après correction"""
    output_file = tmp_path / "corrected_output.csv"

    # Corriger le fichier
    correct_csv(
        INPUT_FILE,
        output_file,
        delimiter=';',
        show_progress=False
    )

    # Mapping des colonnes pour le schéma 'individu'
    column_mapping = {
        'id_anonymized_membre': 2,
        'sexe': 3,
        'date_naissance': 4,
        'role_menage': 5,
        'id_anonymized_chef': 1,
    }

    # Lire le CSV corrigé
    df = pd.read_csv(output_file, delimiter=';', dtype=str, keep_default_na=False, header=None)

    # Créer un DataFrame avec les colonnes mappées
    df_mapped = pd.DataFrame()
    for schema_col, csv_index in column_mapping.items():
        if csv_index < len(df.columns):
            df_mapped[schema_col] = df.iloc[:, csv_index]

    # Conversions
    df_mapped['sexe'] = df_mapped['sexe'].map({'M': 'Homme', 'F': 'Femme', '': ''})

    # Convertir role_menage en int
    df_mapped['role_menage'] = pd.to_numeric(df_mapped['role_menage'], errors='coerce').fillna(0).astype(int)

    # Convertir dates JJ/MM/AA en JJ/MM/AAAA
    def convert_date(date_str):
        if pd.isna(date_str) or date_str == '':
            return date_str
        parts = date_str.split('/')
        if len(parts) == 3:
            jour, mois, annee_2ch = parts
            annee_int = int(annee_2ch)
            annee_4ch = 2000 + annee_int if annee_int < 50 else 1900 + annee_int
            return f"{jour}/{mois}/{annee_4ch}"
        return date_str

    df_mapped['date_naissance'] = df_mapped['date_naissance'].apply(convert_date)

    # Ajouter 'lib' vide (non présent dans ce CSV)
    df_mapped['lib'] = ''

    # Valider avec le schéma Pandera
    import colums_validator
    schema = colums_validator.schema_by_table['individu']

    try:
        schema.validate(df_mapped)
        # Si on arrive ici, la validation a réussi
    except Exception as e:
        pytest.fail(f"Validation Pandera échouée: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

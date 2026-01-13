"""Tests pour le script de conversion TXT vers CSV"""
from pathlib import Path

import pytest

from convert_txt_to_csv import convert_txt_to_csv, detect_encoding


# Chemin vers les fichiers de test dans fixtures
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
SOURCE_DIR = FIXTURES_DIR / "input" / "source"
CSV_DIR = FIXTURES_DIR / "input" / "csv"


def test_source_dir_exists():
    """Vérifie que le répertoire source existe"""
    assert SOURCE_DIR.exists(), f"Le répertoire source {SOURCE_DIR} n'existe pas"
    assert SOURCE_DIR.is_dir(), f"{SOURCE_DIR} n'est pas un répertoire"


def test_csv_dir_exists():
    """Vérifie que le répertoire csv existe"""
    assert CSV_DIR.exists(), f"Le répertoire csv {CSV_DIR} n'existe pas"
    assert CSV_DIR.is_dir(), f"{CSV_DIR} n'est pas un répertoire"


def test_detect_encoding():
    """Test de la détection d'encodage"""
    # Créer un fichier de test simple
    test_file = SOURCE_DIR / "test_encoding.txt"
    test_content = "Test content with émojis 🎉"
    
    try:
        # Écrire en UTF-8
        test_file.write_text(test_content, encoding='utf-8')
        
        # Détecter l'encodage
        encoding = detect_encoding(test_file)
        
        # L'encodage devrait être utf-8 ou ascii
        assert encoding in ['utf-8', 'ascii', 'Windows-1252'], \
            f"Encodage détecté inattendu: {encoding}"
    finally:
        if test_file.exists():
            test_file.unlink()


def test_convert_txt_to_csv():
    """Test de la conversion TXT vers CSV"""
    # Nettoyer le répertoire csv avant le test
    for csv_file in CSV_DIR.glob("*.csv"):
        csv_file.unlink()
    
    # Vérifier qu'il y a un fichier .txt dans source
    txt_files = list(SOURCE_DIR.glob("*.txt"))
    if not txt_files:
        pytest.skip("Aucun fichier .txt trouvé dans le répertoire source")
    
    # Convertir
    convert_txt_to_csv(SOURCE_DIR, CSV_DIR)
    
    # Vérifier que des fichiers CSV ont été créés
    csv_files = list(CSV_DIR.glob("*.csv"))
    assert len(csv_files) > 0, "Aucun fichier CSV créé"
    
    # Vérifier que les noms de fichiers ont les espaces remplacés par _
    for csv_file in csv_files:
        assert ' ' not in csv_file.name, \
            f"Le nom de fichier {csv_file.name} contient encore des espaces"
        assert csv_file.suffix == '.csv', \
            f"Le fichier {csv_file.name} n'a pas l'extension .csv"
        
        # Vérifier que le fichier n'est pas vide
        assert csv_file.stat().st_size > 0, \
            f"Le fichier {csv_file.name} est vide"
        
        # Vérifier que le fichier est en UTF-8 (peut être lu avec UTF-8)
        try:
            content = csv_file.read_text(encoding='utf-8')
            assert len(content) > 0, "Le contenu est vide"
        except UnicodeDecodeError:
            pytest.fail(f"Le fichier {csv_file.name} n'est pas en UTF-8")


def test_convert_file_with_spaces():
    """Test spécifique pour les fichiers avec espaces dans le nom"""
    # Chercher un fichier avec espaces
    txt_files_with_spaces = [f for f in SOURCE_DIR.glob("*.txt") if ' ' in f.name]
    
    if not txt_files_with_spaces:
        pytest.skip("Aucun fichier avec espaces trouvé")
    
    # Nettoyer le répertoire csv
    for csv_file in CSV_DIR.glob("*.csv"):
        csv_file.unlink()
    
    # Convertir
    convert_txt_to_csv(SOURCE_DIR, CSV_DIR)
    
    # Vérifier qu'un fichier correspondant a été créé
    for txt_file in txt_files_with_spaces:
        expected_csv_name = txt_file.stem.replace(' ', '_') + '.csv'
        expected_csv_file = CSV_DIR / expected_csv_name
        
        assert expected_csv_file.exists(), \
            f"Le fichier CSV attendu {expected_csv_name} n'a pas été créé"
        
        # Vérifier que le contenu est identique (sauf encodage)
        txt_content = txt_file.read_text(encoding=detect_encoding(txt_file))
        csv_content = expected_csv_file.read_text(encoding='utf-8')
        
        # Normaliser les fins de ligne pour la comparaison
        txt_content = txt_content.replace('\r\n', '\n').replace('\r', '\n')
        csv_content = csv_content.replace('\r\n', '\n').replace('\r', '\n')
        
        assert txt_content == csv_content, \
            "Le contenu du fichier CSV ne correspond pas au fichier TXT original"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

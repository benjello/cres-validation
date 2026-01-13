"""Script pour convertir les fichiers .txt du répertoire source en .csv dans le répertoire csv"""
from pathlib import Path

import chardet

from config import get_config


def detect_encoding(file_path: Path) -> str:
    """
    Détecte l'encodage d'un fichier texte.

    Args:
        file_path: Chemin vers le fichier

    Returns:
        Encodage détecté (par défaut 'utf-8')
    """
    # Lire un échantillon du fichier pour détecter l'encodage
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # Lire les 10 premiers KB

    if not raw_data:
        return 'utf-8'

    # Détecter l'encodage avec chardet
    result = chardet.detect(raw_data)
    encoding = result.get('encoding', 'utf-8')
    confidence = result.get('confidence', 0)

    # Si la confiance est faible, essayer utf-8 en premier
    if confidence < 0.7:
        try:
            with open(file_path, encoding='utf-8') as f:
                f.read()
            return 'utf-8'
        except UnicodeDecodeError:
            pass

    # Essayer l'encodage détecté
    try:
        with open(file_path, encoding=encoding) as f:
            f.read()
        return encoding
    except (UnicodeDecodeError, LookupError):
        # Si l'encodage détecté ne fonctionne pas, essayer latin-1 (qui accepte tous les bytes)
        return 'latin-1'


def convert_txt_to_csv(source_dir: Path, csv_dir: Path) -> None:
    """
    Convertit tous les fichiers .txt du répertoire source en .csv dans le répertoire csv.

    Args:
        source_dir: Répertoire contenant les fichiers .txt
        csv_dir: Répertoire de destination pour les fichiers .csv
    """
    if not source_dir.exists():
        print(f"⚠️  Le répertoire source n'existe pas: {source_dir}")
        return

    if not source_dir.is_dir():
        print(f"⚠️  {source_dir} n'est pas un répertoire")
        return

    # Créer le répertoire de destination s'il n'existe pas
    csv_dir.mkdir(parents=True, exist_ok=True)

    # Trouver tous les fichiers .txt
    txt_files = sorted(source_dir.glob("*.txt"))
    txt_files.extend(sorted(source_dir.glob("*.TXT")))  # Aussi les fichiers en majuscules

    if not txt_files:
        print(f"ℹ️  Aucun fichier .txt trouvé dans {source_dir}")
        return

    print(f"📁 {len(txt_files)} fichier(s) .txt trouvé(s) dans {source_dir}")
    print("=" * 60)

    for txt_file in txt_files:
        # Détecter l'encodage
        encoding = detect_encoding(txt_file)
        print(f"\n📄 Fichier: {txt_file.name}")
        print(f"   Encodage détecté: {encoding}")

        # Créer le nouveau nom de fichier (remplacer espaces par _ et changer extension)
        new_name = txt_file.stem.replace(' ', '_') + '.csv'
        csv_file = csv_dir / new_name

        try:
            # Lire le fichier avec l'encodage détecté
            with open(txt_file, encoding=encoding) as infile:
                content = infile.read()

            # Remplacer les délimiteurs ; par , (sans corriger les lignes incomplètes)
            content = content.replace(';', ',')
            
            # Écrire en UTF-8 dans le fichier CSV
            with open(csv_file, 'w', encoding='utf-8') as outfile:
                outfile.write(content)

            print(f"   ✅ Converti: {csv_file.name}")
            print(f"   📊 Taille: {txt_file.stat().st_size:,} bytes → {csv_file.stat().st_size:,} bytes")

        except Exception as e:
            print(f"   ❌ Erreur lors de la conversion: {e}")

    print("\n" + "=" * 60)
    print(f"✅ Conversion terminée: {len(txt_files)} fichier(s) traité(s)")


if __name__ == "__main__":
    config = get_config()
    input_dir = config.get_path("paths", "input_dir")
    source_dir = input_dir / "source"
    csv_dir = input_dir / "csv"

    print(f"📂 Répertoire source: {source_dir}")
    print(f"📂 Répertoire CSV: {csv_dir}")
    print()

    convert_txt_to_csv(source_dir, csv_dir)

import csv
import logging
from collections import Counter
from pathlib import Path


def count_columns_in_line_fast(line: str, delimiter: str = ',') -> int:
    """
    Compte rapidement le nombre de colonnes dans une ligne CSV.
    Version optimisée qui évite de créer un reader CSV pour chaque ligne.

    Args:
        line: Ligne du fichier CSV
        delimiter: Délimiteur utilisé (par défaut ',')

    Returns:
        int: Nombre de colonnes détectées
    """
    # Version rapide : parsing manuel simple pour la plupart des cas
    # Si la ligne contient des guillemets, utiliser csv.reader
    if '"' in line or "'" in line:
        reader = csv.reader([line], delimiter=delimiter)
        try:
            row = next(reader)
            return len(row)
        except Exception:
            # Fallback: compter les délimiteurs
            return line.count(delimiter) + 1
    else:
        # Pas de guillemets : compter simplement les délimiteurs (beaucoup plus rapide)
        return line.count(delimiter) + 1


def analyze_csv_columns(
    csv_path: Path,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    use_most_frequent: bool = True,
    show_progress: bool = True,
    chunk_size: int = 100000,
    logger: logging.Logger | None = None
) -> tuple[int, list[int], Counter]:
    """
    Analyse un fichier CSV pour détecter les lignes avec un nombre de colonnes incorrect.
    Version optimisée pour les gros fichiers (millions de lignes).

    Args:
        csv_path: Chemin vers le fichier CSV
        delimiter: Délimiteur utilisé (par défaut ',')
        encoding: Encodage du fichier (par défaut 'utf-8')
        use_most_frequent: Si True, utilise le nombre de colonnes le plus fréquent.
                          Si False, utilise le nombre de colonnes le plus grand.
        show_progress: Afficher une barre de progression
        chunk_size: Nombre de lignes à traiter avant d'afficher la progression
        logger: Logger optionnel (utilise print() si None)

    Returns:
        Tuple contenant:
        - Le nombre de colonnes attendu
        - Liste des numéros de lignes avec un nombre de colonnes incorrect
        - Counter avec la répartition des colonnes
        - Dictionnaire {line_num: col_count} des lignes problématiques
    """
    if logger is None:
        logger = logging.getLogger('cres-validation')
    # PREMIÈRE PASSE : déterminer le nombre de colonnes attendu
    # On ne stocke QUE les comptages, pas toutes les lignes
    column_counter = Counter()
    total_lines = 0
    empty_lines = 0

    def read_file_with_encoding(enc: str):
        nonlocal total_lines, empty_lines, column_counter
        column_counter.clear()
        total_lines = 0
        empty_lines = 0
        is_first_line = True

        with open(csv_path, encoding=enc, newline='', buffering=8192*16) as f:
            for _line_num, line in enumerate(f, start=1):
                stripped = line.rstrip('\n\r')
                if not stripped.strip():
                    empty_lines += 1
                    continue

                # Ignorer le header (première ligne qui ressemble à un header)
                if is_first_line:
                    if stripped.startswith(';') and ('matricul' in stripped.lower() or 'cin' in stripped.lower()):
                        is_first_line = False
                        continue
                    is_first_line = False

                total_lines += 1
                col_count = count_columns_in_line_fast(stripped, delimiter)
                column_counter[col_count] += 1

                if show_progress and total_lines % chunk_size == 0:
                    logger.debug(f"Première passe: {total_lines:,} lignes analysées...")

    try:
        read_file_with_encoding(encoding)
    except UnicodeDecodeError:
        if show_progress:
            logger.debug("Tentative avec encodage latin-1...")
        try:
            read_file_with_encoding('latin-1')
        except Exception as e:
            raise ValueError(f"Impossible de lire le fichier: {e}") from e

    if show_progress:
        logger.debug(f"Première passe terminée: {total_lines:,} lignes analysées")

    if not column_counter:
        raise ValueError("Le fichier CSV est vide ou ne contient que des lignes vides")

    # Déterminer le nombre de colonnes attendu
    if use_most_frequent:
        expected_columns = column_counter.most_common(1)[0][0]
    else:
        expected_columns = max(column_counter.keys())

    # DEUXIÈME PASSE : identifier uniquement les lignes problématiques
    # On stocke les numéros de lignes ET leur nombre de colonnes
    problematic_lines = {}  # {line_num: col_count}

    def find_problematic_lines(enc: str):
        nonlocal problematic_lines
        problematic_lines = {}
        current_line = 0

        with open(csv_path, encoding=enc, newline='', buffering=8192*16) as f:
            for line_num, line in enumerate(f, start=1):
                stripped = line.rstrip('\n\r')
                if not stripped.strip():
                    continue

                current_line += 1
                col_count = count_columns_in_line_fast(stripped, delimiter)

                if col_count != expected_columns:
                    problematic_lines[line_num] = col_count

                if show_progress and current_line % chunk_size == 0:
                    logger.debug(f"Deuxième passe: {current_line:,} lignes, {len(problematic_lines):,} problématiques...")

    if show_progress:
        logger.debug(f"Identification des lignes problématiques (attendu: {expected_columns} colonnes)...")

    try:
        find_problematic_lines(encoding)
    except UnicodeDecodeError:
        find_problematic_lines('latin-1')

    # Convertir en liste triée pour compatibilité, mais on garde aussi le dict
    problematic_lines_list = sorted(problematic_lines.keys())
    return expected_columns, problematic_lines_list, column_counter, problematic_lines


def validate_csv(
    csv_path: Path,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    show_progress: bool = True,
    max_problematic_display: int = 100,
    logger: logging.Logger | None = None
) -> None:
    """
    Valide un fichier CSV et affiche les lignes problématiques.
    Version optimisée pour les gros fichiers.

    Args:
        csv_path: Chemin vers le fichier CSV
        delimiter: Délimiteur utilisé (par défaut ',')
        encoding: Encodage du fichier (par défaut 'utf-8')
        show_progress: Afficher la progression
        max_problematic_display: Nombre maximum de lignes problématiques à afficher
        logger: Logger optionnel (utilise print() si None)
    """
    if logger is None:
        logger = logging.getLogger('cres-validation')

    logger.info(f"Analyse du fichier: {csv_path}")
    logger.debug(f"Délimiteur: '{delimiter}'")
    logger.info("-" * 60)

    try:
        # Essayer d'abord avec le nombre de colonnes le plus fréquent
        expected_cols, problematic_lines_list, column_counter, problematic_lines_dict = analyze_csv_columns(
            csv_path, delimiter, encoding, use_most_frequent=True, show_progress=show_progress, logger=logger
        )

        total_lines = sum(column_counter.values())
        logger.info(f"Nombre de colonnes attendu (le plus fréquent): {expected_cols}")
        logger.info(f"Nombre total de lignes analysées: {total_lines:,}")

        if problematic_lines_list:
            logger.warning(f"{len(problematic_lines_list):,} ligne(s) avec un nombre de colonnes incorrect")

            # Afficher seulement les premières lignes problématiques avec leur nombre de colonnes
            if len(problematic_lines_list) <= max_problematic_display:
                logger.info("Détails des lignes problématiques:")
                for line_num in problematic_lines_list:
                    actual_cols = problematic_lines_dict[line_num]
                    logger.info(f"  Ligne {line_num:,}: {actual_cols} colonne(s) (attendu: {expected_cols})")
            else:
                logger.info(f"Premières {max_problematic_display} lignes problématiques:")
                for line_num in problematic_lines_list[:max_problematic_display]:
                    actual_cols = problematic_lines_dict[line_num]
                    logger.info(f"  Ligne {line_num:,}: {actual_cols} colonne(s) (attendu: {expected_cols})")
                logger.info(f"... et {len(problematic_lines_list) - max_problematic_display:,} autres lignes")
                logger.debug("Pour sauvegarder toutes les lignes problématiques, utilisez save_problematic_lines()")

            # Afficher les statistiques
            logger.info("Répartition du nombre de colonnes:")
            for col_count, freq in column_counter.most_common():
                marker = "✓" if col_count == expected_cols else "✗"
                percentage = (freq / total_lines) * 100
                logger.info(f"  {marker} {col_count} colonne(s): {freq:,} ligne(s) ({percentage:.2f}%)")
        else:
            logger.info("Toutes les lignes ont le bon nombre de colonnes!")

        # Optionnel: vérifier aussi avec le nombre de colonnes le plus grand
        max_cols = max(column_counter.keys())
        if max_cols != expected_cols:
            max_cols_count = column_counter[max_cols]
            logger.debug(f"Nombre de colonnes maximum: {max_cols} ({max_cols_count:,} ligne(s))")
            if max_cols_count < len(problematic_lines_list):
                logger.debug(f"Si vous utilisez {max_cols} comme référence, "
                           f"{max_cols_count:,} ligne(s) seraient correctes")

    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {e}", exc_info=True)


def save_problematic_lines(
    csv_path: Path,
    output_path: Path,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    logger: logging.Logger | None = None
) -> None:
    """
    Sauvegarde les numéros de lignes problématiques dans un fichier.

    Args:
        csv_path: Chemin vers le fichier CSV à analyser
        output_path: Chemin vers le fichier de sortie
        delimiter: Délimiteur utilisé
        encoding: Encodage du fichier
        logger: Logger optionnel
    """
    if logger is None:
        logger = logging.getLogger('cres-validation')

    logger.info("Analyse en cours...")
    expected_cols, problematic_lines_list, column_counter, problematic_lines_dict = analyze_csv_columns(
        csv_path, delimiter, encoding, use_most_frequent=True, show_progress=True, logger=logger
    )

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Lignes problématiques du fichier: {csv_path}\n")
        f.write(f"# Nombre de colonnes attendu: {expected_cols}\n")
        f.write(f"# Total de lignes problématiques: {len(problematic_lines_list)}\n")
        f.write("# Format: ligne_numéro, nombre_colonnes\n")
        f.write("#\n")
        for line_num in sorted(problematic_lines_list):
            actual_cols = problematic_lines_dict[line_num]
            f.write(f"{line_num},{actual_cols}\n")

    logger.info(f"{len(problematic_lines_list):,} lignes problématiques sauvegardées dans: {output_path}")


def correct_csv(
    csv_path: Path,
    output_path: Path,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    show_progress: bool = True,
    chunk_size: int = 100000,
    logger: logging.Logger | None = None
) -> None:
    """
    Corrige un fichier CSV en supprimant les retours à la ligne intempestifs
    qui causent un nombre de colonnes incorrect.

    La stratégie : fusionner les lignes qui ont moins de colonnes que le nombre attendu
    (le plus fréquent et le plus grand) avec les lignes suivantes jusqu'à obtenir
    le bon nombre de colonnes.

    Args:
        csv_path: Chemin vers le fichier CSV à corriger
        output_path: Chemin vers le fichier CSV corrigé
        delimiter: Délimiteur utilisé
        encoding: Encodage du fichier
        show_progress: Afficher la progression
        chunk_size: Nombre de lignes à traiter avant d'afficher la progression
        logger: Logger optionnel (utilise print() si None)
    """
    if logger is None:
        logger = logging.getLogger('cres-validation')

    logger.info(f"Correction du fichier: {csv_path}")
    logger.info(f"Fichier de sortie: {output_path}")
    logger.info("-" * 60)

    # D'abord, analyser pour déterminer le nombre de colonnes attendu
    if show_progress:
        logger.info("Analyse du fichier pour déterminer le nombre de colonnes attendu...")

    expected_cols_freq, _, column_counter, _ = analyze_csv_columns(
        csv_path, delimiter, encoding, use_most_frequent=True, show_progress=False, logger=logger
    )
    expected_cols_max = max(column_counter.keys())

    # Utiliser le maximum entre le plus fréquent et le plus grand
    expected_columns = max(expected_cols_freq, expected_cols_max)

    logger.info(f"Nombre de colonnes attendu: {expected_columns} (fréquent: {expected_cols_freq}, max: {expected_cols_max})")

    # Compter le nombre de lignes dans le fichier original
    original_lines_count = 0
    try:
        with open(csv_path, encoding=encoding, newline='') as f:
            for line in f:
                if line.strip():  # Ignorer les lignes vides
                    original_lines_count += 1
    except UnicodeDecodeError:
        with open(csv_path, encoding='latin-1', newline='') as f:
            for line in f:
                if line.strip():
                    original_lines_count += 1

    logger.debug(f"Nombre de lignes dans le fichier original: {original_lines_count:,}")

    # Créer le répertoire de sortie si nécessaire
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Fonction pour lire avec gestion d'encodage
    def read_and_correct(enc: str):
        lines_written = 0
        lines_corrected = 0
        current_buffer = ""  # Buffer pour accumuler les lignes incomplètes
        original_line_count = 0  # Nombre de lignes originales fusionnées
        is_first_line = True  # Pour détecter le header

        with open(csv_path, encoding=enc, newline='', buffering=8192*16) as infile, \
             open(output_path, 'w', encoding=enc, newline='', buffering=8192*16) as outfile:

            for _line_num, line in enumerate(infile, start=1):
                # Détecter et préserver le header (première ligne qui commence par ;matricul ou similaire)
                if is_first_line:
                    stripped_first = line.rstrip('\n\r')
                    # Si la première ligne ressemble à un header (commence par ; et contient des noms de colonnes)
                    if stripped_first.startswith(';') and ('matricul' in stripped_first.lower() or 'cin' in stripped_first.lower()):
                        # Écrire le header tel quel
                        outfile.write(line)
                        lines_written += 1
                        is_first_line = False
                        continue
                    is_first_line = False
                # Ajouter la ligne au buffer
                if current_buffer:
                    # Fusionner avec la ligne précédente (remplacer le \n par un espace)
                    current_buffer = current_buffer.rstrip('\n\r') + ' ' + line
                    original_line_count += 1
                else:
                    current_buffer = line
                    original_line_count = 1

                stripped = current_buffer.rstrip('\n\r')

                # Ignorer les lignes vides complètes
                if not stripped.strip():
                    current_buffer = ""
                    original_line_count = 0
                    continue

                # Compter les colonnes dans le buffer actuel
                col_count = count_columns_in_line_fast(stripped, delimiter)

                if col_count == expected_columns:
                    # Ligne complète : l'écrire
                    outfile.write(current_buffer)
                    lines_written += 1
                    # Si on a fusionné plusieurs lignes, c'est une correction
                    if original_line_count > 1:
                        lines_corrected += 1
                    current_buffer = ""
                    original_line_count = 0
                elif col_count < expected_columns:
                    # Ligne incomplète : continuer à accumuler
                    # Ne pas écrire encore, attendre la ligne suivante
                    continue
                else:
                    # Plus de colonnes que prévu : problème, écrire quand même
                    # (peut-être un champ avec des délimiteurs ou une erreur)
                    outfile.write(current_buffer)
                    lines_written += 1
                    if original_line_count > 1:
                        lines_corrected += 1
                    current_buffer = ""
                    original_line_count = 0

                if show_progress and lines_written % chunk_size == 0:
                    logger.debug(f"Traité {lines_written:,} lignes écrites, {lines_corrected:,} corrigées...")

            # Écrire le buffer restant s'il y en a un (ligne incomplète à la fin)
            if current_buffer.strip():
                outfile.write(current_buffer)
                lines_written += 1
                if original_line_count > 1:
                    lines_corrected += 1

        return lines_written, lines_corrected

    # Essayer avec l'encodage spécifié, puis latin-1 si nécessaire
    try:
        lines_written, lines_corrected = read_and_correct(encoding)
    except UnicodeDecodeError:
        if show_progress:
            logger.debug("Tentative avec encodage latin-1...")
        lines_written, lines_corrected = read_and_correct('latin-1')

    # Compter le nombre total de lignes dans le fichier corrigé
    total_lines_corrected = 0
    try:
        with open(output_path, encoding=encoding, newline='') as f:
            for line in f:
                if line.strip():  # Ignorer les lignes vides
                    total_lines_corrected += 1
    except UnicodeDecodeError:
        with open(output_path, encoding='latin-1', newline='') as f:
            for line in f:
                if line.strip():
                    total_lines_corrected += 1

    logger.info(f"Fichier corrigé: {output_path}")
    logger.info(f"Lignes dans le fichier original: {original_lines_count:,}")
    logger.info(f"Lignes écrites: {lines_written:,}")
    logger.info(f"Lignes corrigées: {lines_corrected:,}")
    logger.info(f"Nombre total de lignes dans le fichier corrigé: {total_lines_corrected:,}")

    # Résumé final
    reduction = original_lines_count - total_lines_corrected
    if reduction > 0:
        logger.info(f"Résumé: {original_lines_count:,} lignes → {total_lines_corrected:,} lignes ({reduction:,} lignes fusionnées)")
    elif reduction < 0:
        logger.warning(f"Résumé: {original_lines_count:,} lignes → {total_lines_corrected:,} lignes (augmentation inattendue)")
    else:
        logger.info(f"Résumé: {original_lines_count:,} lignes → {total_lines_corrected:,} lignes (aucun changement)")


if __name__ == "__main__":
    from config import get_config

    try:
        config = get_config()
        csv_path = config.get_path("paths", "input_file")
        validate_csv(csv_path)
    except Exception as e:
        print(f"Erreur: {e}")
        print("\nUsage: python csv_validator.py <chemin_vers_fichier.csv>")

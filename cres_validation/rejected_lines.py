"""Module pour sauvegarder les lignes rejetées dans un fichier CSV"""

import logging
from pathlib import Path


def save_rejected_lines_to_csv(
    csv_path: Path,
    rejected_lines: list[tuple[int, str]],
    output_path: Path,
    delimiter: str = ";",
    encoding: str = "utf-8",
    logger: logging.Logger | None = None,
) -> None:
    """
    Sauvegarde les lignes rejetées dans un fichier CSV.

    Args:
        csv_path: Chemin vers le fichier CSV source
        rejected_lines: Liste de tuples (numéro_ligne, contenu_ligne)
        output_path: Chemin vers le fichier CSV de sortie pour les lignes rejetées
        delimiter: Délimiteur utilisé
        encoding: Encodage du fichier
        logger: Logger optionnel
    """
    if logger is None:
        logger = logging.getLogger("cres-validation")

    if not rejected_lines:
        logger.debug("Aucune ligne rejetée à sauvegarder")
        return

    # Créer le répertoire de sortie si nécessaire
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Lire le header du fichier source
    header = None
    try:
        with open(csv_path, encoding=encoding, newline="") as f:
            first_line = f.readline()
            if first_line.strip():
                header = first_line.rstrip("\n\r")
    except UnicodeDecodeError:
        try:
            with open(csv_path, encoding="latin-1", newline="") as f:
                first_line = f.readline()
                if first_line.strip():
                    header = first_line.rstrip("\n\r")
        except Exception:
            pass

    # Écrire les lignes rejetées dans le fichier CSV
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        # Écrire le header si disponible
        if header:
            f.write(header + "\n")

        # Écrire les lignes rejetées
        for _line_num, line_content in rejected_lines:
            # Nettoyer la ligne (retirer les retours à la ligne)
            cleaned_line = line_content.rstrip("\n\r")
            if cleaned_line.strip():  # Ignorer les lignes vides
                f.write(cleaned_line + "\n")

    logger.info(f"✅ {len(rejected_lines)} ligne(s) rejetée(s) sauvegardée(s) dans: {output_path.name}")

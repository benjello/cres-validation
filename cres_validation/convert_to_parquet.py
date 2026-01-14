"""Module pour convertir les fichiers CSV corrigés en format Parquet"""

import logging
from pathlib import Path

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False


def convert_csv_to_parquet(
    csv_path: Path,
    parquet_path: Path,
    delimiter: str = ";",
    logger: logging.Logger | None = None,
) -> None:
    """
    Convertit un fichier CSV en format Parquet.

    Args:
        csv_path: Chemin vers le fichier CSV source
        parquet_path: Chemin vers le fichier Parquet de destination
        delimiter: Délimiteur utilisé dans le CSV (par défaut ';')
        logger: Logger optionnel pour les messages

    Raises:
        ImportError: Si pandas ou pyarrow ne sont pas installés
        FileNotFoundError: Si le fichier CSV n'existe pas
    """
    if logger is None:
        logger = logging.getLogger("cres-validation.parquet")
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    if not PARQUET_AVAILABLE:
        raise ImportError(
            "Les dépendances pour Parquet ne sont pas installées. "
            "Installez pandas et pyarrow: pip install pandas pyarrow"
        )

    if not csv_path.exists():
        raise FileNotFoundError(f"Le fichier CSV n'existe pas: {csv_path}")

    try:
        # Lire le CSV
        logger.debug(f"Lecture du fichier CSV: {csv_path}")
        df = pd.read_csv(csv_path, delimiter=delimiter, dtype=str, keep_default_na=False)

        # Créer le répertoire de destination s'il n'existe pas
        parquet_path.parent.mkdir(parents=True, exist_ok=True)

        # Convertir en Parquet
        logger.debug(f"Conversion en Parquet: {parquet_path}")
        table = pa.Table.from_pandas(df)
        pq.write_table(table, parquet_path)

        csv_size = csv_path.stat().st_size
        parquet_size = parquet_path.stat().st_size
        compression_ratio = (1 - parquet_size / csv_size) * 100 if csv_size > 0 else 0

        logger.debug(
            f"Conversion terminée: {csv_size:,} bytes → {parquet_size:,} bytes "
            f"({compression_ratio:.1f}% de compression)"
        )

    except Exception as e:
        logger.error(f"Erreur lors de la conversion en Parquet: {e}", exc_info=True)
        raise

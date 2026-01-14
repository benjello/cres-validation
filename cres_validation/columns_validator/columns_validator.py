"""Validation des colonnes avec schéma Pandera"""

import logging
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaError

from cres_validation.columns_validator.helpers import convert_date_jjmmaa_to_jjmmaaaa
from cres_validation.columns_validator.schemas import schemas


def validate_csv_columns(
    csv_path: Path,
    delimiter: str = ";",
    schema_name: str | None = None,
    schema_to_use: pa.DataFrameSchema | None = None,
    logger: logging.Logger | None = None,
) -> bool:
    """
    Valide les colonnes d'un CSV avec un schéma Pandera en utilisant le header pour mapper les colonnes.

    Args:
        csv_path: Chemin vers le fichier CSV
        delimiter: Délimiteur utilisé
        schema_name: Nom du schéma à utiliser (ex: "cnrps"). Si None, utilise schema_to_use
        schema_to_use: Schéma Pandera à utiliser directement. Ignoré si schema_name est fourni

    Returns:
        True si la validation réussit, False sinon
    """
    # Déterminer le schéma à utiliser
    if schema_name is not None:
        if schema_name not in schemas:
            available = ", ".join(schemas.keys())
            raise ValueError(f"Schéma '{schema_name}' introuvable. Schémas disponibles: {available}")
        schema_to_use = schemas[schema_name]
    elif schema_to_use is None:
        # Par défaut, utiliser le schéma "cnrps"
        schema_to_use = schemas["cnrps"]

    if logger is None:
        logger = logging.getLogger("cres-validation.pandera")
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    logger.info(f"Validation du fichier: {csv_path}")
    logger.debug(f"Délimiteur: '{delimiter}'")
    logger.debug("-" * 60)

    try:
        # Lire le CSV avec header pour obtenir les noms de colonnes
        logger.debug("Lecture du fichier CSV...")
        df_with_header = pd.read_csv(
            csv_path, delimiter=delimiter, dtype=str, keep_default_na=False, nrows=1
        )

        # Vérifier si le header existe
        has_header = False
        if len(df_with_header.columns) > 0:
            first_col_name = str(df_with_header.columns[0]).strip()
            # Le header commence généralement par le délimiteur ou contient 'matricul'
            if first_col_name.startswith(delimiter) or first_col_name == "" or "matricul" in str(df_with_header.columns).lower():
                has_header = True

        if has_header:
            # Lire avec header
            df = pd.read_csv(
                csv_path, delimiter=delimiter, dtype=str, keep_default_na=False, header=0
            )
            logger.debug(f"Header détecté: {len(df.columns)} colonnes")
            logger.debug(f"  Colonnes: {', '.join(df.columns[:5].tolist())}...")
        else:
            # Lire sans header
            df = pd.read_csv(
                csv_path, delimiter=delimiter, dtype=str, keep_default_na=False, header=None
            )
            logger.debug(f"Aucun header détecté: {len(df.columns)} colonnes")

        logger.debug(f"Nombre de lignes: {len(df)}")

        if len(df) == 0:
            logger.error("Aucune donnée à valider")
            return False

        # Préparer les données pour la validation
        logger.debug("Préparation des données...")

        # Créer un DataFrame avec les colonnes nommées selon le schéma
        df_mapped = pd.DataFrame()

        # Mapping des colonnes du schéma vers les colonnes du CSV
        schema_columns = list(schema_to_use.columns.keys())
        missing_columns = []

        for col_name in schema_columns:
            if col_name in df.columns:
                df_mapped[col_name] = df[col_name]
                logger.debug(f"  {col_name} <- colonne '{col_name}'")
            else:
                missing_columns.append(col_name)
                logger.debug(f"  Colonne '{col_name}': absente du CSV")

        if missing_columns:
            logger.error(f"Colonnes manquantes: {', '.join(missing_columns)}")
            return False

        # Conversions spéciales avant validation
        date_columns = ["date_naissance", "date_affiliation", "date_recrut"]
        for date_col in date_columns:
            if date_col in df_mapped.columns:
                logger.debug(f"  Conversion des dates '{date_col}': JJ/MM/AA -> JJ/MM/AAAA")
                df_mapped[date_col] = df_mapped[date_col].apply(convert_date_jjmmaa_to_jjmmaaaa)

        # Filtrer les lignes où date_naissance ne ressemble pas à une date (colonne principale)
        if "date_naissance" in df_mapped.columns:
            date_mask = df_mapped["date_naissance"].str.contains(r"\d{1,2}/\d{1,2}/\d{4}", na=False)
            non_date_count = (~date_mask).sum()
            if non_date_count > 0:
                logger.warning(f"{non_date_count} ligne(s) avec date_naissance invalide ignorée(s)")
            df_mapped = df_mapped[date_mask].reset_index(drop=True)

        if len(df_mapped) == 0:
            logger.error("Aucune ligne valide après filtrage")
            return False

        # Conversions de types pour les colonnes numériques
        # Colonnes int obligatoires
        required_int_columns = ["matricul", "CIN", "sitfam"]
        for col_name in required_int_columns:
            if col_name in df_mapped.columns:
                df_mapped[col_name] = pd.to_numeric(df_mapped[col_name], errors="coerce").astype("Int64")
                null_count = df_mapped[col_name].isna().sum()
                if null_count > 0:
                    logger.warning(f"{null_count} valeur(s) null dans '{col_name}', remplacée(s) par 0")
                    df_mapped[col_name] = df_mapped[col_name].fillna(0).astype(int)
                else:
                    df_mapped[col_name] = df_mapped[col_name].astype(int)

        # Colonnes int optionnelles (nullable=True dans le schéma)
        optional_int_columns = [
            "postal",
            "pos_admin",
            "code_etab_payeur",
            "code_grade",
            "code_fonction",
            "annee",
            "periode",
        ] + [f"code_indem{i}" for i in range(1, 21)] + [f"montant_indem{i}" for i in range(1, 21)]

        for col_name in optional_int_columns:
            if col_name in df_mapped.columns:
                df_mapped[col_name] = pd.to_numeric(df_mapped[col_name], errors="coerce").astype("Int64")

        logger.debug(f"Lignes à valider: {len(df_mapped)}")

        # Valider avec le schéma Pandera
        logger.debug("Validation avec le schéma Pandera...")
        try:
            schema_to_use.validate(df_mapped)
            logger.info("Validation Pandera réussie : toutes les colonnes sont valides")
            return True
        except SchemaError as e:
            logger.error("Erreur de validation Pandera:")
            logger.error(str(e))
            return False

    except Exception as e:
        logger.error(f"Erreur lors de la lecture/validation: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import sys

    from cres_validation.config import get_config

    # Utiliser le schéma "cnrps" par défaut
    schema_name = "cnrps"

    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if len(sys.argv) > 2:
            schema_name = sys.argv[2]
    else:
        config = get_config()
        csv_path = (
            config.get_path("paths", "input_dir") / "echantillon_cnrps_pb_fondation_fidaa.csv"
        )

    if not csv_path.exists():
        print(f"❌ Fichier introuvable: {csv_path}")
        exit(1)

    success = validate_csv_columns(csv_path, delimiter=",", schema_name=schema_name)
    exit(0 if success else 1)

"""Schémas Pandera pour la validation des colonnes CSV"""

import pandera.pandas as pa

from cres_validation.columns_validator.helpers import vectorized_date_validator_jjmmaaaa


def _create_indemnite_columns(num_indemnites: int = 20) -> dict[str, pa.Column]:
    """
    Crée les colonnes d'indemnités (code_indem et montant_indem).

    Args:
        num_indemnites: Nombre d'indemnités (par défaut: 20)

    Returns:
        Dictionnaire de colonnes Pandera pour les indemnités
    """
    columns = {}
    for i in range(1, num_indemnites + 1):
        columns[f"code_indem{i}"] = pa.Column(int, nullable=True)
        columns[f"montant_indem{i}"] = pa.Column(int, nullable=True)
    return columns


# Schéma complet basé sur le header du fichier de test
# Header: matricul;CIN;sexe;date_naissance;sitfam;postal;date_affiliation;date_recrut;pos_admin;code_etab_payeur;libelle_etab;;code_grade;code_fonction;annee;periode;perd;code_indem1;montant_indem1;...
schema_cnrps = pa.DataFrameSchema(
    columns={
        # Colonnes principales
        "matricul": pa.Column(int),
        "CIN": pa.Column(int),
        "sexe": pa.Column(str),
        "date_naissance": pa.Column(
            str,
            checks=pa.Check(
                vectorized_date_validator_jjmmaaaa,
                element_wise=False,
                error="La colonne doit contenir des dates au format JJ/MM/AAAA valides",
            ),
        ),
        "sitfam": pa.Column(int),
        # Colonnes administratives
        "postal": pa.Column(int, nullable=True),
        "date_affiliation": pa.Column(
            str,
            checks=pa.Check(
                vectorized_date_validator_jjmmaaaa,
                element_wise=False,
                error="La colonne doit contenir des dates au format JJ/MM/AAAA valides",
            ),
            nullable=True,
        ),
        "date_recrut": pa.Column(
            str,
            checks=pa.Check(
                vectorized_date_validator_jjmmaaaa,
                element_wise=False,
                error="La colonne doit contenir des dates au format JJ/MM/AAAA valides",
            ),
            nullable=True,
        ),
        "pos_admin": pa.Column(int, nullable=True),
        "code_etab_payeur": pa.Column(int, nullable=True),
        "libelle_etab": pa.Column(str, nullable=True),
        # Colonnes de classification
        "code_grade": pa.Column(int, nullable=True),
        "code_fonction": pa.Column(int, nullable=True),
        "annee": pa.Column(int, nullable=True),
        "periode": pa.Column(int, nullable=True),
        "perd": pa.Column(str, nullable=True),
        # Indemnités (code_indem1 à code_indem20, montant_indem1 à montant_indem20)
        **_create_indemnite_columns(num_indemnites=20),
    },
    strict=False,  # Permettre des colonnes supplémentaires (comme la colonne vide)
)

# Dictionnaire de tous les schémas disponibles
schemas = {
    "cnrps": schema_cnrps,
}

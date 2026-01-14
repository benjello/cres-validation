from functools import partial

import pandas as pd
import pandera.pandas as pa

DATE_MIN = 1900
DATE_MAX = 2025


def vectorized_date_validator(series, date_format):
    """Vérifie que les dates sont au format JJ/MM/AAAA et valides de façon vectorisée"""
    # Vérifier d'abord que toutes les valeurs sont des chaînes
    if not pd.api.types.is_string_dtype(series):
        return pd.Series([False] * len(series))

    # Vectorisation de la vérification du format avec regex

    if date_format == "jj/mm/aaaa":
        mask_format = series.str.match(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/\d{4}$")
    elif date_format == "aaaa-mm-jj":
        mask_format = series.str.match(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$")
    else:
        raise ValueError(f"Format de date non reconnu: {date_format}")

    # Pour les chaînes qui correspondent au format, extraire jour, mois, année
    valid_format = series[mask_format]
    if len(valid_format) == 0:
        return mask_format  # Retourne False pour toutes les entrées

    # Extraction vectorisée des composants

    if date_format == "jj/mm/aaaa":
        jour = valid_format.str.split("/", expand=True)[0].astype(int)
        mois = valid_format.str.split("/", expand=True)[1].astype(int)
        annee = valid_format.str.split("/", expand=True)[2].astype(int)
    elif date_format == "aaaa-mm-jj":
        annee = valid_format.str.split("-", expand=True)[0].astype(int)
        mois = valid_format.str.split("-", expand=True)[1].astype(int)
        jour = valid_format.str.split("-", expand=True)[2].astype(int)

    # Création d'un masque pour les dates valides
    # Vérification des mois à 30 jours
    mask_30j = (mois.isin([4, 6, 9, 11])) & (jour <= 30)
    # Vérification des mois à 31 jours
    mask_31j = (mois.isin([1, 3, 5, 7, 8, 10, 12])) & (jour <= 31)

    # Calcul vectorisé des années bissextiles
    bissextile = ((annee % 4 == 0) & (annee % 100 != 0)) | (annee % 400 == 0)

    # Vérification pour février
    mask_fevrier = (mois == 2) & ((bissextile & (jour <= 29)) | (~bissextile & (jour <= 28)))

    # Vérification marge date
    superieur_annee_minimale = annee > DATE_MIN
    superieur_annee_maximale = annee <= DATE_MAX
    # Combinaison des masques
    valid_dates = (mask_30j | mask_31j | mask_fevrier) & (
        superieur_annee_minimale & superieur_annee_maximale
    )

    if date_format == "aaaa-mm-jj":
        valid_dates = valid_dates

    # Création du résultat final
    result = pd.Series([False] * len(series))
    result[mask_format.index[mask_format]] = valid_dates

    return result


vectorized_date_validator_jjmmaaaa = partial(vectorized_date_validator, date_format="jj/mm/aaaa")
vectorized_date_validator_aaaammjj = partial(vectorized_date_validator, date_format="aaaa-mm-jj")


schema_by_table = {}

schema_by_table["individu"] = pa.DataFrameSchema(
    columns={
        "date_naissance": pa.Column(
            str,
            pa.Check(
                vectorized_date_validator_jjmmaaaa,
                element_wise=False,  # Important: indique que la fonction traite toute la série
                error="La colonne doit contenir des dates au format JJ/MM/AAAA valides",
            ),
        ),
        "id_anonymized_chef": pa.Column(str),
        "id_anonymized_membre": pa.Column(str),
        "role_menage": pa.Column(int, pa.Check.isin(range(21))),
        "lib": pa.Column(str, pa.Check.isin(["", "خطان", "خط واحد", "3 خطوط"])),
        "sexe": pa.Column(str, pa.Check.isin(["Homme", "Femme"])),
    },
    unique=["id_anonymized_chef", "id_anonymized_membre"],
)

schema_by_table["menage"] = pa.DataFrameSchema(
    columns={
        "id_anonymized_chef": pa.Column(str),
        # 'id_gouv': pa.Column(int),
        # 'id_del':  pa.Column(int),
        "date_modif": pa.Column(
            str,
            pa.Check(
                vectorized_date_validator_aaaammjj,
                element_wise=False,  # Important: indique que la fonction traite toute la série
                error="La colonne doit contenir des dates au format AAAA-MM-JJ valides",
            ),
            nullable=True,
        ),
    },
    # unique = ['id_anonymized_chef'],
)

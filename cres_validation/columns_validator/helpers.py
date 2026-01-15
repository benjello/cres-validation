"""Fonctions helper pour la validation des colonnes"""

from functools import partial

import pandas as pd

# Constantes pour la validation des dates
DATE_MIN = 1900
DATE_MAX = 2025


def vectorized_date_validator(series, date_format):
    """
    Vérifie que les dates sont au format JJ/MM/AAAA ou AAAA-MM-JJ et valides de façon vectorisée.

    Args:
        series: Série pandas contenant les dates à valider
        date_format: Format de date ("jj/mm/aaaa" ou "aaaa-mm-jj")

    Returns:
        Série pandas de booléens indiquant si chaque date est valide
    """
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

    # Création du résultat final
    result = pd.Series([False] * len(series))
    result[mask_format.index[mask_format]] = valid_dates

    return result


# Validateurs de dates pré-configurés
vectorized_date_validator_jjmmaaaa = partial(vectorized_date_validator, date_format="jj/mm/aaaa")
vectorized_date_validator_aaaammjj = partial(vectorized_date_validator, date_format="aaaa-mm-jj")


def convert_date_jjmmaa_to_jjmmaaaa(date_str: str) -> str:
    """
    Convertit une date du format JJ/MM/AA vers JJ/MM/AAAA.

    Args:
        date_str: Date au format JJ/MM/AA

    Returns:
        Date au format JJ/MM/AAAA
    """
    if pd.isna(date_str) or date_str == "":
        return date_str
    parts = date_str.split("/")
    if len(parts) == 3:
        jour, mois, annee_2ch = parts
        # Convertir l'année 2 chiffres en 4 chiffres (assumer 1900-2099)
        annee_int = int(annee_2ch)
        annee_4ch = 2000 + annee_int if annee_int < 50 else 1900 + annee_int
        return f"{jour}/{mois}/{annee_4ch}"
    return date_str


def convert_sexe_mf_to_homme_femme(sexe_str: str) -> str:
    """
    Convertit le sexe de M/F vers Homme/Femme.

    Args:
        sexe_str: Sexe au format M ou F

    Returns:
        Sexe au format Homme ou Femme
    """
    mapping = {"M": "Homme", "F": "Femme", "": ""}
    return mapping.get(sexe_str, sexe_str)


def convert_role_menage_to_int(role_str: str | float, default: int = 0) -> int:
    """
    Convertit role_menage en entier, avec valeur par défaut pour les valeurs vides.

    Args:
        role_str: Valeur de role_menage (peut être str, float, ou NaN)
        default: Valeur par défaut si vide ou invalide

    Returns:
        Entier représentant le role_menage
    """
    # Gérer les valeurs NaN (float('nan'))
    if pd.isna(role_str):
        return default
    # Gérer les chaînes vides
    if isinstance(role_str, str) and role_str.strip() == "":
        return default
    # Convertir en entier
    try:
        return int(float(role_str))
    except (ValueError, TypeError):
        return default

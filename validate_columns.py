"""Script pour valider les colonnes d'un CSV avec les schémas Pandera"""
import sys
from pathlib import Path
import pandas as pd
import colums_validator
from pandera.errors import SchemaError


def validate_csv_columns(csv_path: Path, delimiter: str = ';', table_name: str = 'individu', 
                         column_mapping: dict = None):
    """
    Valide les colonnes d'un CSV avec les schémas Pandera.
    
    Args:
        csv_path: Chemin vers le fichier CSV
        delimiter: Délimiteur utilisé
        table_name: Nom du schéma à utiliser ('individu' ou 'menage')
        column_mapping: Mapping des colonnes CSV vers les colonnes du schéma
                       {nom_colonne_schema: index_colonne_csv}
    """
    print(f"Validation du fichier: {csv_path}")
    print(f"Schéma utilisé: {table_name}")
    print(f"Délimiteur: '{delimiter}'")
    print("-" * 60)
    
    # Vérifier que le schéma existe
    if table_name not in colums_validator.schema_by_table:
        available = list(colums_validator.schema_by_table.keys())
        raise ValueError(f"Schéma '{table_name}' introuvable. Schémas disponibles: {available}")
    
    schema = colums_validator.schema_by_table[table_name]
    
    try:
        # Lire le CSV sans en-tête
        print("Lecture du fichier CSV...")
        df = pd.read_csv(csv_path, delimiter=delimiter, dtype=str, keep_default_na=False, header=None)
        
        print(f"Nombre de lignes: {len(df)}")
        print(f"Nombre de colonnes: {len(df.columns)}")
        
        # Si un mapping est fourni, renommer les colonnes
        if column_mapping:
            print(f"\nApplication du mapping des colonnes...")
            # Créer un DataFrame avec les colonnes renommées
            df_mapped = pd.DataFrame()
            for schema_col, csv_index in column_mapping.items():
                if csv_index < len(df.columns):
                    df_mapped[schema_col] = df.iloc[:, csv_index]
                    print(f"  {schema_col} <- colonne [{csv_index}]")
                else:
                    print(f"⚠️  Index {csv_index} hors limites pour la colonne {schema_col}")
            
            # Conversions spéciales
            if 'sexe' in df_mapped.columns:
                # Convertir M/F en Homme/Femme
                df_mapped['sexe'] = df_mapped['sexe'].map({'M': 'Homme', 'F': 'Femme', '': ''})
                print("  Conversion sexe: M->Homme, F->Femme")
            
            if 'role_menage' in df_mapped.columns:
                # Convertir en int, remplacer les valeurs vides par 0 ou NaN selon le schéma
                df_mapped['role_menage'] = pd.to_numeric(df_mapped['role_menage'], errors='coerce').astype('Int64')
                # Remplacer NaN par une valeur par défaut si nécessaire (0 pour role_menage)
                if df_mapped['role_menage'].isna().any():
                    print(f"  ⚠️  {df_mapped['role_menage'].isna().sum()} valeur(s) null trouvée(s) dans role_menage")
                    # Remplacer par 0 (valeur par défaut valide pour role_menage qui doit être dans range(21))
                    df_mapped['role_menage'] = df_mapped['role_menage'].fillna(0).astype(int)
                    print("  Remplacé les valeurs null par 0")
                else:
                    df_mapped['role_menage'] = df_mapped['role_menage'].astype(int)
                print("  Conversion role_menage en int")
            
            if 'date_naissance' in df_mapped.columns:
                # Convertir JJ/MM/AA en JJ/MM/AAAA
                def convert_date(date_str):
                    if pd.isna(date_str) or date_str == '':
                        return date_str
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        jour, mois, annee_2ch = parts
                        # Convertir l'année 2 chiffres en 4 chiffres (assumer 1900-2099)
                        annee_int = int(annee_2ch)
                        if annee_int < 50:
                            annee_4ch = 2000 + annee_int
                        else:
                            annee_4ch = 1900 + annee_int
                        return f"{jour}/{mois}/{annee_4ch}"
                    return date_str
                
                df_mapped['date_naissance'] = df_mapped['date_naissance'].apply(convert_date)
                print("  Conversion date_naissance: JJ/MM/AA -> JJ/MM/AAAA")
            
            # Ajouter les colonnes manquantes avec des valeurs par défaut
            required_cols = set(schema.columns.keys())
            missing_cols = required_cols - set(df_mapped.columns)
            for col in missing_cols:
                if col == 'lib':
                    # 'lib' peut être vide selon le schéma
                    df_mapped[col] = ''
                    print(f"  Ajout colonne '{col}' avec valeur par défaut (vide)")
                else:
                    df_mapped[col] = None
                    print(f"  Ajout colonne '{col}' avec valeur par défaut (None)")
            
            df = df_mapped
        else:
            # Essayer de détecter automatiquement les colonnes
            # Pour le schéma 'individu', on cherche les colonnes attendues
            required_cols = list(schema.columns.keys())
            print(f"\n⚠️  Aucun mapping fourni. Colonnes requises: {required_cols}")
            print(f"Colonnes disponibles (indices 0-{len(df.columns)-1}):")
            for i in range(min(10, len(df.columns))):
                sample_value = df.iloc[0, i] if len(df) > 0 else ""
                print(f"  [{i}]: {sample_value}")
            return False
        
        print(f"Colonnes mappées: {list(df.columns)}")
        
        # Vérifier que les colonnes requises existent
        required_cols = set(schema.columns.keys())
        actual_cols = set(df.columns)
        missing_cols = required_cols - actual_cols
        
        if missing_cols:
            print(f"\n⚠️  Colonnes manquantes: {missing_cols}")
            return False
        
        # Valider avec le schéma
        print("\nValidation avec le schéma Pandera...")
        try:
            validated_df = schema.validate(df)
            print("✅ Validation réussie ! Toutes les colonnes sont valides.")
            return True
        except SchemaError as e:
            print(f"❌ Erreur de validation:")
            print(str(e))
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la lecture/validation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    from config import get_config
    
    # Mapping des colonnes pour le schéma 'individu'
    # Basé sur la structure observée: ;numéro;id_membre;sexe;date_naissance;role;...
    # Note: 'lib' peut ne pas être présent dans ce CSV, on le laisse vide si nécessaire
    INDIVIDU_COLUMN_MAPPING = {
        'id_anonymized_membre': 2,  # Colonne 2: id (8350684, 6527831...)
        'sexe': 3,  # Colonne 3: M ou F (à convertir en 'Homme'/'Femme')
        'date_naissance': 4,  # Colonne 4: date au format JJ/MM/AA
        'role_menage': 5,  # Colonne 5: role (2, 1...)
        'id_anonymized_chef': 1,  # Colonne 1: numéro (peut-être l'id du chef?)
        # 'lib' n'est pas dans ce CSV, on le laissera vide
    }
    
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        table_name = sys.argv[2] if len(sys.argv) > 2 else 'individu'
        column_mapping = INDIVIDU_COLUMN_MAPPING if table_name == 'individu' else None
    else:
        # Utiliser le fichier de test par défaut
        config = get_config()
        csv_path = config.get_path("paths", "input_dir") / "echantillon_cnrps_pb_fondation_fidaa.csv"
        table_name = 'individu'
        column_mapping = INDIVIDU_COLUMN_MAPPING
    
    if not csv_path.exists():
        print(f"❌ Fichier introuvable: {csv_path}")
        sys.exit(1)
    
    success = validate_csv_columns(csv_path, delimiter=';', table_name=table_name, column_mapping=column_mapping)
    sys.exit(0 if success else 1)

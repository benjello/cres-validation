"""Package cres_validation - Validation et correction de fichiers CSV pour le projet CRES"""

__version__ = "0.1.0"

# Exports publics
from cres_validation.columns_number_validator import (
    analyze_csv_columns,
    correct_csv,
    validate_csv,
)
from cres_validation.config import get_config
from cres_validation.convert_txt_to_csv import (
    convert_txt_file_to_csv,
    convert_txt_to_csv,
    detect_encoding,
)

__all__ = [
    "get_config",
    "analyze_csv_columns",
    "correct_csv",
    "validate_csv",
    "convert_txt_to_csv",
    "convert_txt_file_to_csv",
    "detect_encoding",
]

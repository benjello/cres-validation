import configparser
import os
import shutil
from pathlib import Path


class ConfigReader:
    """Lecteur de configuration pour lire les chemins de fichiers depuis config.ini"""

    def __init__(self, config_path: Path | None = None):
        """
        Initialise le lecteur de configuration.

        Args:
            config_path: Chemin vers le fichier config.ini.
                        Si None, utilise ~/.config/cres-validation/config.ini
        """
        self.config = configparser.ConfigParser()

        if config_path is None:
            # Utilise le répertoire de config utilisateur
            config_path = Path.home() / ".config" / "cres-validation" / "config.ini"

        self.config_path = Path(config_path)
        self._load_config()

    def _load_config(self) -> None:
        """Charge le fichier de configuration"""
        if not self.config_path.exists():
            # Créer le répertoire de configuration si nécessaire
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Trouver le config.ini du paquet (dans le même répertoire que config.py)
            package_dir = Path(__file__).parent
            package_config = package_dir / "config.ini"

            if package_config.exists():
                # Copier le config.ini du paquet vers le répertoire utilisateur
                shutil.copy2(package_config, self.config_path)
                print(f"✓ Fichier de configuration créé: {self.config_path}")
            else:
                raise FileNotFoundError(
                    f"Le fichier de configuration n'a pas été trouvé: {self.config_path}\n"
                    f"Et le fichier template {package_config} est introuvable."
                )

        self.config.read(self.config_path, encoding="utf-8")

    def get_path(self, section: str, key: str) -> Path:
        """
        Récupère un chemin de fichier depuis la configuration.

        Args:
            section: Section du fichier INI (ex: 'paths', 'data')
            key: Clé dans la section (ex: 'input_file', 'output_dir')

        Returns:
            Path: Chemin vers le fichier/dossier

        Raises:
            KeyError: Si la section ou la clé n'existe pas
        """
        if not self.config.has_section(section):
            raise KeyError(f"Section '{section}' introuvable dans {self.config_path}")

        if not self.config.has_option(section, key):
            raise KeyError(f"Option '{key}' introuvable dans la section '{section}'")

        path_str = self.config.get(section, key)
        return Path(path_str).expanduser().resolve()

    def get_paths(self, section: str) -> dict[str, Path]:
        """
        Récupère tous les chemins d'une section.

        Args:
            section: Section du fichier INI

        Returns:
            dict: Dictionnaire {clé: Path} pour tous les chemins de la section
        """
        if not self.config.has_section(section):
            raise KeyError(f"Section '{section}' introuvable dans {self.config_path}")

        return {
            key: Path(value).expanduser().resolve() for key, value in self.config.items(section)
        }

    def get(self, section: str, key: str, fallback: str | None = None) -> str:
        """
        Récupère une valeur de configuration (peut être autre chose qu'un chemin).

        Args:
            section: Section du fichier INI
            key: Clé dans la section
            fallback: Valeur par défaut si la clé n'existe pas

        Returns:
            str: Valeur de la configuration
        """
        return self.config.get(section, key, fallback=fallback)

    def reload(self) -> None:
        """Recharge le fichier de configuration"""
        self._load_config()


# Instance globale pour faciliter l'utilisation
_config_reader: ConfigReader | None = None


def get_config(config_path: Path | None = None) -> ConfigReader:
    """
    Obtient l'instance globale du lecteur de configuration.

    Args:
        config_path: Chemin vers config.ini (utilisé uniquement à la première appel)

    Returns:
        ConfigReader: Instance du lecteur de configuration
    """
    global _config_reader
    if _config_reader is None:
        _config_reader = ConfigReader(config_path)
    return _config_reader


def reset_config() -> None:
    """Réinitialise l'instance globale (utile pour les tests)"""
    global _config_reader
    _config_reader = None


def get_delimiter() -> str:
    """
    Récupère le délimiteur CSV depuis la variable d'environnement Python.

    La variable d'environnement Python utilisée est `CRES_CSV_DELIMITER`
    (accessible via `os.environ`).
    Si elle n'est pas définie, retourne ';' par défaut.

    Note: Cette fonction pourra être étendue à l'avenir pour permettre
    un ajustement fichier par fichier.

    Returns:
        str: Le délimiteur CSV (par défaut ';')
    """
    return os.getenv("CRES_CSV_DELIMITER", ";")

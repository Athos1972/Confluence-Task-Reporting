import toml
import sys


class Singleton(type):
    """
    Singleton-Klasse.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    """
    Globale Konfiguration aus toml-File lesen und zur Verfügung stellen. Singleton-Klasse - wird nur 1x instanziert
    """
    def __init__(self, filename="../config.toml"):
        """

        :param filename: Dateiname (inkl. Pfad - wenn notwendig) zur Konfigurationsdatei
        """
        self.filename = filename
        self.config = toml.load(filename)
        if not self.config:
            sys.exit(f"Config-File {filename} not found")

    def get_config(self, config_key: str, optional=True, default_value=None):
        """
        Gibt den/die Werte aus dem Config-File (TOML) zurück

        :param config_key: Schlüssel, der aus dem Config-File rauskomen soll
        :param optional: Nicht dumpen, wenn der Parameter nicht gefunden wurde
        :param default_value: Wert, der zurückgegeben werden soll wenn nichts gefunden wurde
        :return:
        """
        if optional:
            return self.config.get(config_key, default_value)

        if not self.config.get(config_key):
            raise ValueError(f"Key {config_key} not found in Config. Parameter not optional.")

        return self.config[config_key]

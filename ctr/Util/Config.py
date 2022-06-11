import toml
import sys
from pathlib import Path
import argparse


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
    def __init__(self, filename="config.toml"):
        """

        :param filename: Dateiname (inkl. Pfad - wenn notwendig) zur Konfigurationsdatei
        """
        print(f"CWD = {Path.cwd()}")
        self.filename = filename
        self.config = toml.load(filename)
        self.__get_cli_args()
        if not self.config:
            sys.exit(f"Config-File {filename} not found")

    def __get_cli_args(self):
        """
        Appends CLI Arguments to Config
        :return: Nothing
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-OUWT', '--onlyUserWithTasks')
        # parser.add_argument('-v', dest='verbose', action='store_true')
        args = parser.parse_args()
        self.config["OUWT"] = True if args.onlyUserWithTasks else False


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

        if not config_key in self.config.keys():
            raise ValueError(f"Key {config_key} not found in Config. Parameter not optional.")

        return self.config[config_key]

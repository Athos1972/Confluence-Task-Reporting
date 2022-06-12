import toml
import sys
from pathlib import Path
import argparse


class Singleton(type):
    """
    Singleton-Class. Can have only exactly 1 instance.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    """
    Read and provide global config settings from config.toml, environment and CLI-Parameters.
    Singleton-Klasse - wird nur 1x instanziert
    """
    def __init__(self, filename=None):
        """
        We get Config-filename from CLI-Arguments. If not we fallback to config.toml

        After reading config we re-read CLI-Arguments to make sure they always override settings in the TOML-File.

        :param filename: Filename (incl. full path) to the configuration file
        """
        self.config = {}
        if not filename:
            self.__get_cli_args()
            filename = self.config["CONFIG_FILE"]

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
        parser.add_argument('-c', '--configFile')
        # parser.add_argument('-v', dest='verbose', action='store_true')
        args = parser.parse_args()
        self.config["OUWT"] = True if args.onlyUserWithTasks else False
        self.config["CONFIG_FILE"] = args.configFile or "config.toml"

    def get_config(self, config_key: str, optional=True, default_value=None):
        """
        Returns the value of a configuration parameter.

        :param config_key: Key from the configuration file
        :param optional: If true we don't raise an error when the key is no there
        :param default_value: default value if no value was found in the configuration file
        :return:
        """
        if optional:
            return self.config.get(config_key, default_value)

        if config_key not in self.config.keys():
            raise ValueError(f"Key {config_key} not found in Config. Parameter not optional.")

        return self.config[config_key]

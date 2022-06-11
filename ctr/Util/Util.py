from os import environ
from dotenv import load_dotenv
from ctr.Util import logger, global_config
import sys


class Util:
    """
    Several helper methods.
    """

    @staticmethod
    def load_env_file():
        """
        Ließt das .env-File und schreibt die beiden Parameter conf_user und conf_pwd in das Environment
        Die Parameter werden von der JIRA und CONFLUENCE-Instanz für die Anmeldung verwendet.
        """
        try:
            load_dotenv()
        except FileNotFoundError:
            logger.critical(f"Du hast kein .env-File. Abbruch. Check README.md")
            sys.exit()

        if not environ.get("CONF_USER"):
            logger.critical(f"Im .env-File fehlt die Variable 'CONF_USER'")
            sys.exit("Check log und README.MD (CONF_USER")
        if not environ.get("CONF_PWD"):
            logger.critical(f"Im .env-File fehlt die Variable 'CONF_PWD'")
            sys.exit("Check log und README.MD (CONF_PWD)")

        if environ.get("CONF_BASE_URL"):
            # Übernahme von CONF_BASE_URL aus dem .env-File in die globalen Konstanten.
            global_config.config["CONF_BASE_URL"] = environ["CONF_BASE_URL"]

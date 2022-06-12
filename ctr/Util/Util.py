from os import environ
from dotenv import load_dotenv
from ctr.Util import logger, global_config
import sys
import pandas as pd



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

    @staticmethod
    def write_pd_to_excel(file_name, sheetname, dataframe):
        df = dataframe
        # bissl schöner formatieren als nur mit l_pd.to_excel("increment_summary.xlsx")
        writer = pd.ExcelWriter(file_name, engine='xlsxwriter',
                                engine_kwargs={'options': {'strings_to_numbers': True}})
        df.to_excel(writer, sheet_name=sheetname, index=False)  # send df to writer
        worksheet = writer.sheets[sheetname]          # pull worksheet object
        for spalten_nummer, spalte in enumerate(df):  # loop through all columns
            try:
                series = df[spalte]
                max_len = max((
                    series.astype(str).map(len).max(),  # len of largest item
                    len(str(series.name))               # len of column name/header
                )) + 1                                  # adding a little extra space
                if max_len > 50:
                    max_len = 50                        # No monster columns
                worksheet.set_column(spalten_nummer, spalten_nummer, max_len)  # set column width
            except KeyError as ex:
                logger.warning(f"Weird things during formatting of XLS. Error was: {ex}")
        writer.save()
        return True

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from ctr.Util import global_config, logger
from ctr.Database.model import CreateTableStructures
from pathlib import Path


class SqlConnector:
    """
    Provides the Connection to the database and offers get_session to execute sqlite operations with
    """
    def __init__(self, file=None, *args, **kwargs):
        self.engine = None
        if not file:
            file = global_config.get_config("filename_database", optional=False)
        self.file = str(file)

    def get_engine(self, *args, **kwargs):
        if not self.engine:
            # Check, if the database exists already
            file_exists = Path(self.file.replace("sqlite:///", "").replace("?check_same_thread=False","")).exists()
            self.engine = create_engine(self.file, echo=kwargs.get("echo", False), future=True)
            if not file_exists:
                logger.warning(f"File {self.file} did not exist. Now creating database structures.")
                creator = CreateTableStructures(self.engine)
                creator.create_table_structures()

        return self.engine

    def get_session(self):
        """
        The database Session of sqlalchemy.orm.
        :return: a new session
        """
        return Session(self.get_engine())

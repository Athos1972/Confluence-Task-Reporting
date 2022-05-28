from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from ctr.Util import global_config


class SqlConnector:
    def __init__(self, file=None, *args, **kwargs):
        self.engine = None
        if not file:
            file = global_config.get_config("filename_database", optional=False)
        self.file = file

    def get_engine(self, *args, **kwargs):
        if not self.engine:
            self.engine = create_engine(self.file, echo=kwargs.get("echo", False), future=True)
        return self.engine

    def get_session(self):
        """
        The database Session of sqlalchemy.orm.
        :return: a new session
        """
        return Session(self.get_engine())

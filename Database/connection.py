from sqlalchemy import create_engine


class SqlConnector:
    def __init__(self, file, *args, **kwargs):
        self.engine = None
        self.file = file
        pass

    def get_engine(self, *args, **kwargs):
        if not self.engine:
            self.engine = create_engine(self.file, echo=kwargs.get("echo", False), future=True)
        return self.engine

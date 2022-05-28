from Util.Util import Util
from Util import global_config
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import MetaData
from sqlalchemy.orm import Session
from Database.connection import SqlConnector
from datetime import datetime


Base = declarative_base()


class User(Base):
    __tablename__ = "conf_users"

    id = Column(String(50), primary_key=True)
    conf_name = Column(String(100))
    email = Column(String(255))
    last_crawled = Column(DateTime())

    def __repr__(self):
        return f"User(id={self.id!r}, Name={self.conf_name!r} E-Mail={self.email!r}"

    def __init__(self, id, conf_name, email, last_crawled=None):
        self.id = id
        self.conf_name = conf_name
        self.email = email
        if not last_crawled:
            self.last_crawled = datetime.strptime("1972-02-14", "%Y-%m-%d")
        else:
            self.last_crawled = last_crawled


class Task(Base):
    __tablename__ = "tasks"

    internal_id = Column(Integer, primary_key=True)
    global_id = Column(String(30), nullable=False)
    due_date = Column(DateTime, nullable=True)
    second_date = Column(DateTime, nullable=True)
    is_done = Column(Boolean, nullable=False)
    last_crawled = Column(DateTime(), nullable=True)

    user_id = Column(String(50), ForeignKey("conf_users.id"), nullable=True)
    user = relationship("User", backref="tasks")


class CreateTableStructures:
    def __init__(self, engine):
        self.engine = engine

    def create_table_structures(self):
        Base.metadata.create_all(self.engine)


if __name__ == '__main__':
    Util.load_env_file()
    engine = SqlConnector(file=global_config.get_config("filename_database"))

    createTables = CreateTableStructures(engine=engine.get_engine())
    createTables.create_table_structures()

    lNew = User("franzi6", "Franzi", "franzi@fritzi.com", datetime.now())
    lNew2 = User("fritzi6", "fritzi", "fritzi@franzi.com")

    session = Session(engine.get_engine())
    session.add_all([lNew, lNew2])
    session.commit()
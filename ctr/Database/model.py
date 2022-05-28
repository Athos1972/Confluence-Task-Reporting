from ctr.Util.Util import Util
from ctr.Util import global_config
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
from ctr.Database.connection import SqlConnector
from datetime import datetime


Base = declarative_base()


class User(Base):
    __tablename__ = "conf_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conf_name = Column(String(100))
    conf_userkey = Column(String(100))
    display_name = Column(String(100))
    email = Column(String(255))
    last_crawled = Column(DateTime())

    def __repr__(self):
        return f"User(id={self.id!r}, Name={self.conf_name!r} E-Mail={self.email!r}"

    def __init__(self, conf_name, conf_userkey, email, display_name, last_crawled=None):
        self.conf_name = conf_name
        self.conf_userkey = conf_userkey
        self.email = email
        self.display_name = display_name
        if not last_crawled:
            self.last_crawled = datetime.strptime("1972-02-14", "%Y-%m-%d")
        else:
            self.last_crawled = last_crawled


class Task(Base):
    __tablename__ = "tasks"

    internal_id = Column(Integer, primary_key=True, autoincrement=True)
    global_id = Column(String(30), nullable=False)
    due_date = Column(DateTime, nullable=True)
    second_date = Column(DateTime, nullable=True)
    is_done = Column(Boolean, nullable=False)
    last_crawled = Column(DateTime(), nullable=True)
    page_link = Column(String(50), nullable=False)

    user_id = Column(String(50), ForeignKey("conf_users.id"), nullable=True)
    user = relationship("User", backref="tasks")

    def __init__(self, global_id = global_id):
        self.global_id = global_id


class CreateTableStructures:
    def __init__(self, engine):
        self.engine = engine

    def create_table_structures(self):
        Base.metadata.create_all(self.engine)

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import Boolean
from sqlalchemy import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime

Base = declarative_base()


class ModelDoku:
    """
    This file holds the sqlalchemy-Model. Basically the tables and the fields and a bit of Alchemy.
    """


class User(Base):
    __tablename__ = "conf_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conf_name = Column(String(100), nullable=False)
    conf_userkey = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)  # Might be filled in later!
    last_crawled = Column(DateTime(), onupdate=func.now(), nullable=True)
    tasks_last_crawled = Column(DateTime(), nullable=True)

    def __repr__(self):
        return f"User(id={self.id!r}, Name={self.conf_name!r} E-Mail={self.email!r}"

    def __init__(self, conf_name, conf_userkey, email, display_name, last_crawled=None):
        self.conf_name = conf_name
        self.conf_userkey = conf_userkey
        self.email = email
        self.display_name = display_name
        self.last_crawled = last_crawled

    @hybrid_property
    def company_name(self):
        if not self.email:
            return None
        return self.email.split["@"][1].split(".")[0]


class Task(Base):
    __tablename__ = "tasks"

    internal_id = Column(Integer, primary_key=True, autoincrement=True)
    global_id = Column(String(30), nullable=False)
    due_date = Column(DateTime, nullable=True)
    second_date = Column(DateTime, nullable=True)
    is_done = Column(Boolean, nullable=False)
    last_crawled = Column(DateTime(), onupdate=func.now(), nullable=True)
    task_description = Column(String(), nullable=True)

    user_id = Column(Integer, ForeignKey("conf_users.id"), nullable=True)
    user = relationship("User", backref="tasks")

    page_link = Column(Integer, ForeignKey("page.internal_id"), nullable=False)
    page = relationship("Page", backref="tasks")

    def __init__(self, global_id=global_id):
        self.global_id = global_id

    def __repr__(self):
        return f"Int.ID={self.internal_id!r}, global_id={self.global_id!r}"


class Page(Base):
    __tablename__ = "page"

    internal_id = Column(Integer, primary_key=True, autoincrement=True)
    page_link = Column(String(100), nullable=False)
    page_name = Column(String(200), nullable=False)
    page_id = Column(Integer, nullable=True)
    space = Column(String(50), nullable=True)  # True because Space is not known during initial creation.
    last_crawled = Column(DateTime, onupdate=func.now(), nullable=False)

    def __init__(self, page_link, page_name):
        self.page_link = page_link
        self.page_name = page_name
        self.last_crawled = datetime.now()

    def __repr__(self):
        return f'Name: {self.page_name!r}, ID: {self.page_id}'


class CreateTableStructures:
    """
    Create the Tables in the database, if not already there.
    Existing tables are not updated. New Tables are created.
    """
    def __init__(self, engine):
        self.engine = engine

    def create_table_structures(self):
        Base.metadata.create_all(self.engine)

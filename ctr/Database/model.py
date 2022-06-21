from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import Date
from sqlalchemy import Boolean
from sqlalchemy import func, event
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, date as datetimedate
from ctr.Util import logger

Base = declarative_base()


def _extract_company_from_email(email: str):
    """
    Extracts Company-Name from E-Mail. If length of company-Name is up to 4 digits company name is rendered in upper-
    case, e.g. Ibm looks weird, IBM looks better. Otherwise first character of company-name is translated to upper case
    :param email:
    :return:
    """
    if not email:
        return "unknown"
    if "@" not in email:
        return "unknown"

    # "franzi@fritzi.com"
    company = email.split("@")[1]  # fritzi.com
    company = company.split(".")[0]  # fritzi

    if len(company) <= 4:
        return company.upper()  # Fritzi
    return company.title()


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
    last_crawled = Column(DateTime(), server_onupdate=func.now(), server_default=func.now())
    tasks_last_crawled = Column(DateTime(), nullable=True)
    company = Column(String(100), nullable=True, index=True)

    def __repr__(self):
        return f"User(id={self.id!r}, Name={self.conf_name!r} E-Mail={self.email!r}"

    def __init__(self, conf_name, conf_userkey, email, display_name, last_crawled=None, company="unknown"):
        self.conf_name = conf_name
        self.conf_userkey = conf_userkey
        # Needs to be before email so that it will be overwritten with proper value
        self.company = company
        self.email = email
        self.display_name = display_name
        self.last_crawled = last_crawled


@event.listens_for(User.email, "set")
def update_User_email(target, value, oldvalue, initiator):
    """
    Listens to changes to "User.email" and writes company-field from these changes.
    :param target: the User-class
    :param value: the new value of User.email
    :param oldvalue: The previous value. Not used so far.
    :param initiator: not used so far.
    :return:
    """
    target.company = _extract_company_from_email(value)
    return target


class Task(Base):
    __tablename__ = "tasks"

    internal_id = Column(Integer, primary_key=True, autoincrement=True)
    global_id = Column(String(30), nullable=False)  # GlobalID from Confluence. This is a bit weird as it's not
    # supplied in tasks in pages but only in taskview-API.
    task_id = Column(Integer, nullable=False)  # TaskId on the current page
    reminder_date = Column(Date, nullable=True)  # The first date that can be found in a task
    second_date = Column(Date, nullable=True)  # The second date that can be found in a task
    due_date = Column(Date, nullable=True)  # Calculated due_date
    is_done = Column(Boolean, nullable=False)  # Task incomplete or completed
    first_seen = Column(DateTime(), default=func.now())
    last_crawled = Column(DateTime(), onupdate=func.now(), nullable=True, index=True)
    # The HTML Task Description from the WIKI-PAge
    task_description = Column(String(), nullable=True)

    # Link to user_tasks, who is the owner of the task. Confluence considers only the first mentioned user_tasks
    # as assignee. All other names are just as information
    user_id = Column(Integer, ForeignKey("conf_users.id"), nullable=True)
    user = relationship("User", backref="tasks")

    # Link to the page, where this task can be found
    page_link = Column(Integer, ForeignKey("pages.internal_id"), nullable=False)
    page = relationship("Page", backref="tasks")

    def __init__(self, global_id=global_id):
        self.global_id = global_id

    def __repr__(self):
        return f"Int.ID={self.internal_id!r}, global_id={self.global_id!r}"

    @hybrid_property
    def age(self):
        # This is processed during single record operations
        x = (datetimedate.today() - self.due_date)
        return x

    @age.expression
    def age(cls):
        # FIXME: Works only on SQLITE-DB
        # This is processed during queries with more than one entry
        return func.julianday("now") - func.julianday(cls.due_date)


@event.listens_for(Task.second_date, "set")
def update_due_date_from_second_date(target: Task, value, oldvalue, initiator):
    """
    If second date (=value) is lower than reminder date then this is the due_date.
    If second date (=value) is not filled set the due_date to reminder_date (=1st date)
    :param target:
    :param value:
    :param oldvalue:
    :param initiator:
    :return:
    """
    if not target.reminder_date and value:
        target.due_date = value
        return target
    if value:
        try:
            if value < target.reminder_date:
                target.due_date = value
                return target
        except TypeError:
            logger.critical(f"Received {value}. Target.reminder_date was {target.reminder_date}. Didn't do anything.")
            return target
    if not value:
        target.due_date = target.reminder_date
    return target


@event.listens_for(Task.reminder_date, "set")
def update_due_date_from_reminder_date(target: Task, value, oldvalue, initiator):
    """
    Due date is either the second date (if that one is higher than the reminder date) or the reminder date.
    :param target: the Task-Instance
    :param value: the new value of Task.reminder_date
    :param oldvalue:
    :param initiator:
    :return: the Task-Instance
    """
    if target.second_date:
        if value or datetimedate(year=1972, month=1, day=1) > target.second_date:
            target.due_date = target.second_date
            return target
        target.due_date = value
        return target
    target.due_date = value
    return target


class Page(Base):
    __tablename__ = "pages"

    internal_id = Column(Integer, primary_key=True, autoincrement=True)
    page_link = Column(String(100), nullable=False)  # Link to the page
    page_name = Column(String(200), nullable=False)  # Name/Title of the page
    page_id = Column(Integer, nullable=True, unique=True)  # The unique Confluence PageID
    space = Column(String(50), nullable=True, index=True)  # True because Space is not known during initial creation.
    last_crawled = Column(DateTime, onupdate=func.now(), nullable=False, index=True)

    def __init__(self, page_link, page_name):
        self.page_link = page_link
        self.page_name = page_name
        self.last_crawled = datetime.now()

    def __repr__(self):
        return f'Name: {self.page_name!r}, ID: {self.page_id}'


class Statistics(Base):
    __tablename__ = "stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, nullable=False)
    space = Column(String(50), nullable=False)

    user_id = Column(Integer, ForeignKey("conf_users.id"), nullable=True)
    user = relationship("User", backref="stats")

    overdue = Column(Integer, nullable=True)
    total = Column(Integer, nullable=False)

    def __init__(self, space, date, user_id, overdue, total):
        self.space = space
        self.stat_date = date
        self.user_id = user_id
        self.overdue = overdue
        self.total = total


class CreateTableStructures:
    """
    Create the Tables in the database, if not already there.
    Existing tables are not updated. New Tables are created.
    """

    def __init__(self, engine):
        self.engine = engine

    def create_table_structures(self):
        Base.metadata.create_all(self.engine)

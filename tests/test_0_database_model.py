import os, sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from ctr.Util.Util import Util
from ctr.Database.connection import SqlConnector
from ctr.Database.model import CreateTableStructures
from ctr.Database.model import User, Task, Page
from datetime import datetime, timedelta, date
from random import choices
import string
from ctr.Util import logger, timeit
from pathlib import Path

Util.load_env_file()
db_connection = SqlConnector(file=f"sqlite:///{Path.cwd().joinpath('testdatabase.db')}?check_same_thread=False")
session = db_connection.get_session()


def test_initial_creation_model():
    createTables = CreateTableStructures(engine=db_connection.get_engine())
    createTables.create_table_structures()


def test_create_initial_user():
    start_of_test = datetime.utcnow().replace(microsecond=0)

    q = session.query(User).filter(User.conf_name == "NBUBEV").first()
    if q:
        # User was already created
        q.last_crawled = datetime.utcnow()
    else:
        q = User(conf_name="NBUBEV", conf_userkey="", email="franzi@fritzi.com", display_name="nudlaug")
        session.add(q)
    session.commit()
    assert q.last_crawled >= start_of_test


def test_database_model_page_initial_creation():
    lNew = Page(page_link="123", page_name="123")
    lNew.page_id = int("".join(choices(string.digits, k=15)))
    lNew.space = "franzi"
    l_session = db_connection.get_session()
    l_session.add(lNew)
    l_session.commit()
    assert lNew.internal_id > 0


def test_database_model_user_initial_creation():
    l_session = db_connection.get_session()
    lNew = User(conf_name="Testfranzi", email="franzi@fritzi.com", conf_userkey="", display_name="4711",
                last_crawled=datetime.now())
    lNew2 = User(conf_name="Testfritzi", email="fritzi@franzi.com", conf_userkey="", display_name="0815")

    l_session.add_all([lNew, lNew2])
    try:
        l_session.commit()
    except Exception as ex:
        logger.info(f"Error from Test was {ex}")
    assert l_session.query(User.conf_name).filter(User.conf_name == "Testfranzi").count() > 0


def test_database_model_task_initial_creation():
    """
    Creates one Task on database
    :return:
    """

    l_session = db_connection.get_session()

    lNew = Task(global_id=123)
    lNew.reminder_date = date.today()
    lNew.second_date = date.today()
    lNew.is_done = False
    lNew.task_id = 123354
    lNew.page_link = "dummydummy"
    lNew.user = l_session.query(User).first()
    lNew.page = l_session.query(Page).first()

    l_session.add(lNew)
    l_session.commit()
    assert lNew.internal_id
    assert lNew.due_date == lNew.second_date


def test_task_due_date_is_reminder_date():
    lNew = Task(global_id=1200)
    lNew.reminder_date = date(year=2022, month=12, day=10)
    lNew.second_date = date(year=2022, month=12, day=13)
    lNew.is_done = False
    lNew.task_id = 123
    lNew.page_link = "dummydummy"
    lNew.user = session.query(User).first()
    lNew.page = session.query(Page).first()

    session.add(lNew)
    session.commit()
    assert lNew.due_date == lNew.reminder_date

    lNew.second_date = date(year=2022, month=10, day=10)
    session.commit()
    assert lNew.due_date == lNew.second_date


def test_task_age():
    l_session = db_connection.get_session()
    task = Task(global_id=12345)
    task.is_done = False
    task.task_id = 1234
    task.reminder_date = datetime.now() - timedelta(days=1)
    task.page_link = l_session.query(Task).first().page_link
    l_session.add(task)
    l_session.commit()
    l_id = task.internal_id
    x = l_session.query(Task).filter(Task.internal_id == l_id).first()
    print(f"Age: {x.age}")
    assert x.age >= timedelta(days=1)


def test_user_company_from_email():
    l_session = db_connection.get_session()
    user = User(conf_name="franzi", conf_userkey="fritzi", email="fritzi@franzi.com", display_name="semmal")
    l_session.add(user)
    l_session.commit()
    assert user.company == "Franzi"


@timeit
def test_database_model_create_more_entries_for_users(number_of_entries=100):
    l_session = db_connection.get_session()
    users_to_add = []
    for _ in range(100):
        users_to_add.append(User(conf_name=f"{''.join(choices(string.ascii_letters, k=6))}",
                                 conf_userkey="123",
                                 display_name="123123",
                                 email="dummy@dummy.com"))

    l_session.add_all(users_to_add)
    l_session.commit()
    tuple_of_ids = [x.id for x in users_to_add]
    saved_to_database = l_session.query(User).filter(User.id.in_(tuple_of_ids)).all()
    assert (len(saved_to_database) == len(users_to_add))
    logger.info(f"Commited {number_of_entries} to database.")


if __name__ == '__main__':
    test_task_due_date_is_reminder_date()
    test_user_company_from_email()
    test_initial_creation_model()
    test_database_model_page_initial_creation()
    test_database_model_user_initial_creation()
    test_database_model_task_initial_creation()
    test_create_initial_user()
    test_task_age()
    test_database_model_create_more_entries_for_users(100)

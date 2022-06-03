import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from ctr.Util.Util import Util
from ctr.Util import global_config
from ctr.Database.connection import SqlConnector
from ctr.Database.model import CreateTableStructures
from ctr.Database.model import User, Task, Page
from datetime import datetime, timedelta
from random import choices
import string
from ctr.Util import logger, timeit
from pathlib import Path

Util.load_env_file()
db_connection = SqlConnector(file=f"sqlite:///{Path.cwd().joinpath('testdatabase.db')}")
session = db_connection.get_session()


def test_initial_creation_model():

    createTables = CreateTableStructures(engine=db_connection.get_engine())
    createTables.create_table_structures()


def test_create_initial_user():
    start_of_test = datetime.utcnow()

    q = session.query(User).filter(User.conf_name=="NBUBEV").first()
    if q:
        # User was already created
        q.last_crawled = datetime.utcnow()
    else:
        q = User(conf_name="NBUBEV", conf_userkey = "", email="franzi@fritzi.com", display_name="nudlaug")
        session.add(q)
    session.commit()
    assert q.last_crawled > start_of_test


def test_database_model_page_initial_creation():
    lNew = Page(page_link="123", page_name="123")
    lNew.page_id = 1234123
    lNew.space = "franzi"
    session = db_connection.get_session()
    session.add(lNew)
    session.commit()
    assert lNew.internal_id > 0


def test_database_model_user_initial_creation():
    session = db_connection.get_session()
    lNew = User(conf_name="Testfranzi", email="franzi@fritzi.com", conf_userkey="", display_name="4711",
                last_crawled=datetime.now())
    lNew2 = User(conf_name="Testfritzi", email="fritzi@franzi.com", conf_userkey="", display_name="0815")

    session.add_all([lNew, lNew2])
    try:
        session.commit()
    except Exception as ex:
        logger.info(f"Error from Test was {ex}")
    assert session.query(User.conf_name).filter(User.conf_name=="Testfranzi").count() > 0


def test_database_model_task_initial_creation():
    """
    Creates one Task on database
    :return:
    """

    session = db_connection.get_session()

    lNew = Task(global_id=123)
    lNew.due_date = datetime.now()
    lNew.second_date = datetime.now()
    lNew.is_done = False
    lNew.task_id = 123354
    lNew.page_link = "dummydummy"
    lNew.user = session.query(User).first()
    lNew.page = session.query(Page).first()

    session.add(lNew)
    session.commit()
    assert lNew.internal_id


def test_task_has_second_date_attribute():
    session = db_connection.get_session()
    x = session.query(Task).filter(Task.global_id==123, Task.second_date).first()
    assert x.has_second_date == True


def test_task_has_second_date_attribute_false():
    session = db_connection.get_session()
    task = Task(global_id=124)
    task.is_done = False
    task.page_link = "4711"
    task.task_id = 123
    session.add(task)
    session.commit()
    x = session.query(Task).filter(Task.global_id == 124)
    assert x[0].has_second_date == False


def test_task_age():
    session = db_connection.get_session()
    task = Task(global_id=12345)
    task.is_done = False
    task.task_id = 1234
    task.due_date = datetime.now() - timedelta(days=1)
    task.page_link = session.query(Task).first().page_link
    session.add(task)
    session.commit()
    l_id = task.internal_id
    x = session.query(Task).filter(Task.internal_id==l_id).first()
    print(f"Age: {x.age}")
    assert x.age >= timedelta(days=1)


def test_user_company_from_email():
    session = db_connection.get_session()
    user = User(conf_name="franzi", conf_userkey="fritzi", email="fritzi@franzi.com", display_name="semmal")
    assert user.company == "franzi"


@timeit
def test_database_model_create_more_entries_for_users(number_of_entries=100):

    x = 0
    users_to_add = []
    while x < number_of_entries:
        users_to_add.append(User(conf_name=f"{''.join(choices(string.ascii_letters,k=6))}",
                                 conf_userkey="123",
                                 display_name="123123",
                                 email="dummy@dummy.com"))
        x += 1

    session.add_all(users_to_add)
    session.commit()
    tuple_of_ids = [x.id for x in users_to_add]
    saved_to_database = session.query(User).filter(User.id.in_((tuple_of_ids))).all()
    assert(len(saved_to_database) == len(users_to_add))
    logger.info(f"Commited {number_of_entries} to database.")


if __name__ == '__main__':
    test_initial_creation_model()
    test_database_model_page_initial_creation()
    test_database_model_user_initial_creation()
    test_database_model_task_initial_creation()
    test_create_initial_user()
    test_task_has_second_date_attribute()
    test_task_has_second_date_attribute_false()
    test_user_company_from_email()
    test_task_age()
    test_database_model_create_more_entries_for_users(100)

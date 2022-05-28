from ctr.Util.Util import Util
from ctr.Util import global_config
from ctr.Database.connection import SqlConnector
from ctr.Database.model import CreateTableStructures
from ctr.Database.model import User, Task
from datetime import datetime
from random import choices
import string
from ctr.Util import logger, timeit


def do_init():
    Util.load_env_file()
    db_connection = SqlConnector(file=global_config.get_config("filename_database"))
    return db_connection


def test_database_model_user_initial_creation():
    db_connection = do_init()

    createTables = CreateTableStructures(engine=db_connection.get_engine())
    createTables.create_table_structures()

    lNew = User(conf_name="Franzi6", email="franzi@fritzi.com", conf_userkey="", display_name="4711",
                last_crawled=datetime.now())
    lNew2 = User(conf_name="fritzi8", email="fritzi@franzi.com", conf_userkey="", display_name="0815")

    session = db_connection.get_session()
    session.add_all([lNew, lNew2])
    try:
        session.commit()
    except Exception as ex:
        logger.info(f"Error from Test was {ex}")
    assert session.query(User.conf_name).filter(User.conf_name=="Franzi6").count() > 0


def test_database_model_task_initial_creation():

    db_connection = do_init()
    session = db_connection.get_session()

    lNew = Task(global_id=123)
    lNew.due_date = datetime.now()
    lNew.second_date = datetime.now()
    lNew.user = session.query(User).first()
    lNew.is_done = False
    lNew.page_link = "dummydummy"

    session.add(lNew)
    session.commit()


@timeit
def test_database_model_create_more_entries_for_users(number_of_entries=100):
    db_connection = do_init()

    x = 0
    users_to_add = []
    while x < number_of_entries:
        users_to_add.append(User(conf_name=f"{''.join(choices(string.ascii_letters,k=6))}",
                                 conf_userkey="123",
                                 display_name="123123",
                                 email="dummy"))
        x += 1

    session = db_connection.get_session()
    session.add_all(users_to_add)
    session.commit()
    tuple_of_ids = [x.id for x in users_to_add]
    saved_to_database = session.query(User).filter(User.id.in_((tuple_of_ids))).all()
    assert(len(saved_to_database) == len(users_to_add))
    logger.info(f"Commited {number_of_entries} to database.")


if __name__ == '__main__':
    test_database_model_user_initial_creation()
    test_database_model_task_initial_creation()
    test_database_model_create_more_entries_for_users(100)

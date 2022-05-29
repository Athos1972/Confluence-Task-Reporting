from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Database.connection import SqlConnector
from ctr.Crawler.crawl_confluence import TaskWrapper
from random import randint, choices
from ctr.Util import timeit
import string
from pathlib import Path

from ctr.Util.Util import Util

Util.load_env_file()
test_instance = CrawlConfluence()
db_connection = SqlConnector(file=f"sqlite:///{Path.cwd().joinpath('testdatabase.db')}")
session = db_connection.get_session()


def test_tasks_for_single_user():
    """
    Tests wheter for a specific user we receive 10 Tasks as a result when we request 10 tasks
    :return:
    """
    result = test_instance.crawl_tasks_for_user("NBUBEV", limit=5, max_entries=10)
    assert len(result) == 10


def test_task_wapper_new_task_short_date():
    """
    Tests the wrapper. The Wrapper should return a task-id
    :return:
    """

    wrapper = TaskWrapper(username="Testfranzi",
                          global_id=123,
                          due_date="15 Feb 2022",
                          page_name="Franziska 4711",
                          task_description="123",
                          page_link="123",
                          db_connection=db_connection)
    x = wrapper.update_task_in_database()
    assert x > 0

def test_task_wapper_new_task_long_date():
    """
    Tests the wrapper. The Wrapper should return a task-id
    :return:
    """

    wrapper = TaskWrapper(username="Testfranzi",
                          global_id=123,
                          due_date="15 February 2022",
                          page_name="Franziska 4711",
                          task_description="123",
                          page_link="123",
                          db_connection=db_connection)
    x = wrapper.update_task_in_database()
    assert x > 0

@timeit
def test_task_wrapper_multiple(tasks_to_create=10):
    """
    Create multiple tasks at once.
    :param tasks_to_create: Number of random tasks to be created
    :return:
    """
    for x in 0, tasks_to_create:
        wrapper = TaskWrapper(username="", global_id=randint(1,1000000),
                              page_link="".join(choices(string.ascii_lowercase,k=15)),
                              page_name="franziska 4712",
                              task_description="<html></html>",
                              db_connection=db_connection)
        y = wrapper.update_task_in_database()
        assert y > 0


if __name__ == '__main__':
    test_tasks_for_single_user()
    test_task_wapper_new_task_long_date()
    test_task_wapper_new_task_short_date()
    test_task_wrapper_multiple(100)
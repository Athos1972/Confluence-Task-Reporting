from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Crawler.crawl_confluence import TaskWrapper
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, Page
from datetime import datetime
from random import randint, choices
from ctr.Util import timeit
import string

from ctr.Util.Util import Util

Util.load_env_file()
test_instance = CrawlConfluence()
db_connector = SqlConnector()
session = db_connector.get_session()


def test_tasks_for_single_user():
    """
    Tests wheter for a specific user we receive 10 Tasks as a result when we request 10 tasks
    :return:
    """
    result = test_instance.crawl_tasks_for_user("NBUBEV", limit=5, max_entries=10)
    assert len(result) == 10


def test_task_wapper_new_task():
    """
    Tests the wrapper. The Wrapper should return a task-id
    :return:
    """

    wrapper = TaskWrapper(username="NBUBEV",
                          global_id=123,
                          due_date=datetime.now(),
                          page_name="Franziska 4711",
                          task_description="123",
                          page_link="123")
    x = wrapper.update_task_in_database()
    assert x > 0


@timeit
def test_task_wrapper_multiple(tasks_to_create=10):
    for x in 0, tasks_to_create:
        wrapper = TaskWrapper(username="", global_id=randint(1,1000000),
                              page_link="".join(choices(string.ascii_lowercase,k=15)),
                              page_name="franziska 4712",
                              task_description="<html></html>")
        y = wrapper.update_task_in_database()
        assert y > 0


if __name__ == '__main__':
    # test_single_user()
    test_task_wapper_new_task()
    test_task_wrapper_multiple(100)
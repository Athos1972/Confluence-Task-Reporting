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
    Tests wheter for a specific user_tasks we receive 10 Tasks as a result when we request 10 tasks
    :return:
    """
    result = test_instance.crawl_tasks_for_user("NBUBEV", limit=2, max_entries=4)
    assert len(result) == 4


def test_task_wapper_new_task_short_date():
    """
    Tests the wrapper. The Wrapper should return a task-id
    :return:
    """

    wrapper = TaskWrapper(username="Testfranzi",
                          global_id=123,
                          reminder_date="15 Feb 2022",
                          page_name="Franziska 4711",
                          task_description="123",
                          task_id="1234",
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
                          reminder_date="15 February 2022",
                          page_name="Franziska 4711",
                          task_description="123",
                          task_id = 123,
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

    test_text = """<ul><ac:task>
<ac:task-id>340</ac:task-id>
<ac:task-status>incomplete</ac:task-status>
<ac:task-body><span class="placeholder-inline-tasks"><ac:link><ri:user ri:userkey="123"></ri:user></ac:link>test 
<time datetime="2022-06-10"></time><time datetime="2022-05-05"></time></span></ac:task-body>
</ac:task></ul>"""

    for _ in range(tasks_to_create):
        wrapper = TaskWrapper(username="", global_id=randint(1,1000000),
                              page_link="viewpage.action?pageId=" + "".join(choices(string.digits, k=15)),
                              page_name="franziska 4712",
                              task_id=123,
                              task_description=test_text,
                              reminder_date="2022-05-10",
                              db_connection=db_connection)
        y = wrapper.update_task_in_database()
        assert y > 0


if __name__ == '__main__':
    test_tasks_for_single_user()
    test_task_wapper_new_task_long_date()
    test_task_wapper_new_task_short_date()
    test_task_wrapper_multiple(100)
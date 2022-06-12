from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Crawler.crawl_confluence import UserWrapper
from ctr.Database.connection import SqlConnector
from ctr.Database.model import User
from datetime import datetime
from random import choices
from pathlib import Path
import string

from ctr.Util.Util import Util

Util.load_env_file()
test_instance = CrawlConfluence()
db_connection = SqlConnector(file=f"sqlite:///{Path.cwd().joinpath('testdatabase.db')}")
session = db_connection.get_session()


def test_user_crawl():
    """
    When we search for 10 users in 2 Calls we should receive 10 results.
    :return:
    """
    users = test_instance.crawl_users(limit=5, max_entries=10, start=0)
    assert len(users) == 10


def test_user_crawl_max_users():
    """
    When we access users from 999999 up we should not get a result
    :return:
    """
    users = test_instance.crawl_users(limit=10, max_entries=20, start=999999)
    assert len(users) == 0


def test_user_wrapper_exists():
    """
    Read one entry from Database and update the crawl_time.
    :return:
    """

    time_before_execution = datetime.now()
    q = session.query(User).first()
    wrapper = UserWrapper(confluence_name=q.conf_name,
                          email=q.email,
                          confluence_userkey=q.conf_userkey,
                          display_name=q.display_name,
                          db_connection=db_connection)
    wrapper.update_user_in_database()
    q = session.query(User.last_crawled).first()
    assert q[0] > time_before_execution


def test_user_wrapper_new_user():
    """
    Create a new user_tasks and search for it in the database
    :return:
    """
    rand_user_name = ''.join(choices(string.ascii_letters, k=6))
    wrapper = UserWrapper(confluence_name=rand_user_name,
                          confluence_userkey="123",
                          display_name="123test",
                          email="dummy",
                          db_connection=db_connection)
    wrapper.update_user_in_database()
    q = session.query(User.conf_name).filter(User.conf_name == rand_user_name)
    assert q.count() == 1


def test_get_single_email_for_user():
    """
    check, whether the email-search-feature works
    :return:
    """
    result = test_instance.read_userdetails_for_user("NBUBEV")
    assert result['email']


if __name__ == '__main__':
    # Either call via pytest or execute directly using python test_cralwer_users.py or use your IDE to execute those
    # Tests
    test_user_crawl()
    test_user_crawl_max_users()
    test_get_single_email_for_user()
    test_user_wrapper_exists()
    test_user_wrapper_new_user()

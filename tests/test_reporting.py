from ctr.Reporting.Reporter import TaskReporting
from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Database.connection import SqlConnector
from ctr.Util import timeit
from pathlib import Path
from datetime import date

from ctr.Util.Util import Util

Util.load_env_file()
test_instance = CrawlConfluence()
db_connection = SqlConnector(file=f"sqlite:///{Path.cwd().joinpath('testdatabase.db')}")
# db_connection = SqlConnector()
session = db_connection.get_session()
x = TaskReporting(db_connection=db_connection)


def test_tasks_per_space():
    y = x.task_count_by_space()
    for z in y:
        print(z)


def test_task_count_per_user():
    y = x.task_open_count_by_user()
    for z in y:
        print(z)


def test_task_overdue_per_user():
    y = x.task_overdue_count_by_user()
    print("\nTasks Overdue per User")
    for z in y:
        print(z)


def test_task_age_per_space():
    y = x.tasks_by_age_and_space()
    print("\nTasks per age and Space")
    for z in y:
        print(z)


def test_tasks_companies():
    y = x.companies_from_users()
    print("\nCompanies in E-Mail-Addresses")
    print(y.head())

def test_tasks_by_company():
    y = x.task_count_by_company()
    print("\nTask count by company")
    print(y.head())


@timeit
def test_stats_entries():
    y = x.save_daily_statistics()
    assert y

@timeit
def test_stats_entries_with_date():
    y = x.save_daily_statistics(date_of_statistics=date(year=2022, month=1, day=1))
    assert y

@timeit
def test_stats_entries_with_date_and_delete():
    y = x.save_daily_statistics(date_of_statistics=date(year=2022, month=1, day=1), overwrite=True)
    assert y


if __name__ == '__main__':
    test_stats_entries()
    test_stats_entries_with_date()
    test_stats_entries_with_date_and_delete()
    test_tasks_per_space()
    test_task_count_per_user()
    test_task_overdue_per_user()
    test_task_age_per_space()
    test_tasks_by_company()
    test_tasks_companies()
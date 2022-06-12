from bs4 import BeautifulSoup
from ctr.Util import logger
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, User, Page
from sqlalchemy.sql import func
from sqlalchemy import distinct
from sqlite3 import ProgrammingError
from datetime import datetime
from dateutil import parser
import pandas as pd
import functools


def catch_sql_error(func):
    """
    Decorator for DB-Functions to catch DB-Errors
    :return:
    """

    @functools.wraps(func)
    def _retry(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ProgrammingError as ex:
            logger.warning(f"Cought SQLite ProgammingError during {self.__name__}: {ex}")
        except Exception as ex:
            logger.warning(f"Cought other error: {ex}")

    return _retry


class UserReporting:
    def __init__(self, db_connection: SqlConnector):
        self.db_connection = db_connection
        self.session = self.db_connection.get_session()

    @catch_sql_error
    def get_companies(self):
        stmt = distinct(User.company)

        results = list(self.session.query(stmt))

        q = [row[0] for row in results]

        logger.debug(f"returned {len(q)} entries. Statement was: {str(q)}")
        return q


class PageReporting:
    def __init__(self, db_connection: SqlConnector):
        self.db_connection = db_connection
        self.session = db_connection.get_session()

    @catch_sql_error
    def get_spaces(self):
        stmt = distinct(Page.space)

        results = list(self.session.query(stmt))

        q = [row[0] for row in results]

        logger.debug(f"returned {len(q)} entries. Statement was: {str(q)}")
        return q


class TaskReporting:
    def __init__(self, db_connection: SqlConnector):
        self.db_connection = db_connection

    @catch_sql_error
    def task_count_by_space(self, filter_spaces=[], filter_overdue=False):
        session = self.db_connection.get_session()
        if not filter_overdue:
            date_to_filter = datetime.strptime("2199-12-31", "%Y-%m-%d")
        else:
            date_to_filter = datetime.now()
        if not filter_spaces or len("".join(filter_spaces)) == 0:
            q = session.query(func.count(Task.reminder_date), Page.space). \
                join(Page). \
                filter(Task.is_done == False,
                       Task.reminder_date < date_to_filter). \
                group_by(Page.space)
        else:
            q = session.query(func.count(Task.reminder_date), Page.space). \
                join(Page). \
                filter(Task.is_done == False,
                       Task.reminder_date < date_to_filter,
                       Page.space.in_(filter_spaces)). \
                group_by(Page.space)

        logger.debug(f"returned {q.count()} entries. Statement was: {str(q)}")
        return pd.DataFrame(columns=['count', 'space'], data=list(q))

    def task_open_count_by_user(self):
        session = self.db_connection.get_session()
        q = session.query(User.display_name, func.count(Task.internal_id)). \
            join(Task). \
            filter(Task.is_done == False). \
            group_by(User.display_name)
        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return q

    def task_overdue_count_by_user(self):
        session = self.db_connection.get_session()
        q = session.query(User.display_name, func.count(Task.internal_id)). \
            join(Task). \
            filter(Task.is_done == False, Task.reminder_date < datetime.now()). \
            group_by(User.display_name)
        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return q

    def task_count_by_company(self, filter_companies=None, filter_overdue=False):
        session = self.db_connection.get_session()
        if not filter_overdue:
            date_to_filter = datetime.strptime("2199-12-31", "%Y-%m-%d")
        else:
            date_to_filter = datetime.now()
        if not filter_companies or len("".join(filter_companies)) == 0:
            q = session.query(func.count(Task.internal_id), User.company). \
                join(Task). \
                filter(Task.is_done == False,
                       Task.reminder_date < date_to_filter). \
                group_by(User.company)
        else:
            q = session.query(func.count(Task.internal_id), User.company). \
                join(Task). \
                filter(Task.is_done == False,
                       User.company.in_(filter_companies),
                       Task.reminder_date < date_to_filter). \
                group_by(User.company)

        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return pd.DataFrame(columns=['count', 'company'], data=list(q))

    def companies_from_users(self):
        session = self.db_connection.get_session()
        q = session.query(User.company).distinct()
        return pd.DataFrame(columns=["company"], data=list(q))

    @catch_sql_error
    def tasks_by_age_and_space(self, filter_overdue=False):
        if not filter_overdue:
            stmt = """select age, page_space from 
                    (SELECT round(julianday(CURRENT_TIMESTAMP) - julianday(tasks.reminder_date),0) AS age, 
                    pages.space AS page_space FROM tasks JOIN pages ON pages.internal_id = tasks.page_link 
                    WHERE tasks.is_done = 0 AND tasks.reminder_date) group by age
                    """
        else:
            stmt = """select age, page_space from 
                    (SELECT round(julianday(CURRENT_TIMESTAMP) - julianday(tasks.reminder_date),0) AS age, 
                    pages.space AS page_space FROM tasks JOIN pages ON pages.internal_id = tasks.page_link 
                    WHERE tasks.is_done = 0 AND tasks.reminder_date < DATE()) group by age
                    """
        session = self.db_connection.get_session()
        q = session.execute(stmt)
        result = list(q)
        logger.debug(f"returned {len(result)} entries. Statement was {stmt}")
        ages = []
        spaces = []
        for i in range(len(result)):
            ages.append(result[i][0])
            spaces.append(result[i][1])

        data = {"age": ages, "page_space": spaces}
        return pd.DataFrame(data)

    @staticmethod
    def get_task_as_string(task_string: str) -> str:
        """
        Will parse a confluence task's HTML String into a readable/printable Python string.
        :param task_string: Confluence-Task as HTML:
        <ul class="inline-task-list" data-inline-tasks-content-id="77110850">
            <li data-inline-task-id="54">
                <span class="placeholder-inline-tasks">
                    <a class="confluence-userlink user-mention current-user-mention"
                        data-username="zzz"
                        href="/confluencezzz/display/~zzz"
                        data-linked-resource-id="xyz"
                        data-linked-resource-version="3"
                        data-linked-resource-type="userinfo"
                        data-base-url="https://zzz/confluence-zzz">name_of_user</a>
                do something - here is the task description
                <time datetime="2022-05-31" class="date-upcoming">31 May 2022</time>       # This is the reminder date!
                <time datetime="2025-12-31" class="date-future">31 Dec 2025</time>  
                <br/>BB/18.11.21: Done
                <br/>BB/30.11.21: Done
                </span>
                <span class="placeholder-inline-tasks">
                </span>
            </li>
        </ul>

        :return: readable, printable Python String.
        """
        bs = BeautifulSoup(task_string, features="html.parser")

        # Replace TIME-Tag with string of date.
        for x in bs.findAll("time"):
            x.replaceWith(str(parser.parse(x.attrs.get("datetime")).date()) + " ")

        for x in bs.findAll("ul"):
            x.unwrap()
        for x in bs.findAll("li"):
            x.unwrap()
        for x in bs.findAll("span", attrs={"class": "placeholder-inline-tasks"}):
            x.unwrap()
        for x in bs.findAll("a", attrs={"class": "confluence-userlink"}):
            name = x.text
            x.replaceWith(name)

        result = str(bs)

        replace_table = [
            ["\n", ""],
            ["<br/>", "\r\n"],
            ["&gt;", ">"],
            ["&lt;", "<"]
        ]

        for entry in replace_table:
            result = result.replace(entry[0], entry[1])

        return result

    @catch_sql_error
    def get_tasks_view(self):
        session = self.db_connection.get_session()
        q = session.query(Task.internal_id, Task.task_description, Task.reminder_date,
                          Task.second_date, Task.due_date,
                          User.display_name, Page.space, Page.page_name, Page.page_link, User.company). \
            join(User, Page).where(Page.internal_id == Task.page_link, User.id == Task.user_id, Task.is_done == False)

        logger.debug(f"returned {len(list(q))} entries. Statement was: {str(q)}")

        df = pd.DataFrame(columns=["task_internal_id", "Description", "Reminder", "Second", "Due",
                                   "Name", "Space", "page_name", "Page", "Company"],
                          data=list(q))
        # Convert from datetime-Format to date format
        df["Due"] = pd.to_datetime(df['Due']).dt.date
        df["Second"] = pd.to_datetime(df['Second']).dt.date
        df["Reminder"] = pd.to_datetime(df["Reminder"]).dt.date

        # Convert task description into readable format:
        df["Description"] = df["Description"].apply(self.get_task_as_string)

        return df

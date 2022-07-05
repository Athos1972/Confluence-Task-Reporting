from bs4 import BeautifulSoup
from ctr.Util import logger, global_config
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, User, Page, Statistics
from sqlalchemy.sql import func
from sqlalchemy import distinct
from sqlite3 import ProgrammingError
from datetime import datetime, date
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
    def task_count_by_space(self, filter_spaces=None, filter_overdue=False, filter_date=0, filter_companies=None):
        session = self.db_connection.get_session()
        if not filter_overdue:
            date_to_filter = datetime.strptime("2199-12-31", "%Y-%m-%d")
        else:
            date_to_filter = datetime.now()

        q = session.query(func.count(Task.internal_id), Page.space). \
            join(Page, User). \
            filter(Task.is_done == False). \
            group_by(Page.space)

        if filter_spaces:
            q = q.filter(Page.space.in_(filter_spaces))

        if filter_companies:
            q = q.filter(User.company.in_(filter_companies))

        if filter_date == 1:
            q = q.filter(Task.due_date.is_(None))

        if filter_date == 2:
            q = q.filter(Task.due_date.is_not(None))

        if filter_overdue:
            q = q.filter(Task.reminder_date < date_to_filter)


        logger.debug(f"returned {q.count()} entries. Statement was: {str(q)}")
        result = pd.DataFrame(columns=['count', 'space'], data=list(q))

        return result

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

    def task_count_by_company(self, filter_companies=None, filter_overdue=False, filter_date=0, filter_spaces=None):
        session = self.db_connection.get_session()
        if not filter_overdue:
            date_to_filter = datetime.strptime("2199-12-31", "%Y-%m-%d")
        else:
            date_to_filter = datetime.now()

        q = session.query(func.count(Task.internal_id), User.company). \
                join(Task, Page). \
                filter(Task.is_done == False). \
                group_by(User.company)

        if filter_spaces:
            q = q.filter(Page.space.in_(filter_spaces))

        if filter_companies:
            q = q.filter(User.company.in_(filter_companies))

        if filter_date == 1:
            q = q.filter(Task.due_date.is_(None))

        if filter_date == 2:
            q = q.filter(Task.due_date.is_not(None))

        if filter_overdue:
            q = q.filter(Task.reminder_date < date_to_filter)

        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return pd.DataFrame(columns=['count', 'company'], data=list(q))

    def companies_from_users(self):
        session = self.db_connection.get_session()
        q = session.query(User.company).distinct()
        return pd.DataFrame(columns=["company"], data=list(q))

    @catch_sql_error
    def task_count_by_age(self, filter_companies=None, filter_spaces=None, filter_overdue=False):

        overdue_stmt = ""
        space_stmt = ""
        company_stmt = ""

        if filter_companies:
            company_stmt = "AND conf_users.company IN (" + ', '.join('"{}"'.format(t) for t in filter_companies) + ")"
        if filter_spaces:
            space_stmt = "AND pages.space IN (" + ', '.join('"{}"'.format(t) for t in filter_spaces) + ")"
        if filter_overdue:
            overdue_stmt = "AND age < 0"

        stmt = f"""SELECT - round(julianday(current_timestamp) - julianday(tasks.due_date), 0) as age,
        tasks.due_date as date,
        tasks.due_date as count from tasks
        join conf_users on tasks.user_id = conf_users.id
        join pages on tasks.page_link = pages.internal_id
        WHERE tasks.is_done = 0 AND tasks.due_date IS NOT NULL {space_stmt} {company_stmt} {overdue_stmt}
        ORDER BY age"""

        session = self.db_connection.get_session()
        q = session.execute(stmt)

        result = list(q)
        logger.debug(f"returned {len(result)} entries. Statement was {stmt}")
        dataframe = pd.DataFrame(columns=['age', 'date', 'count'], data=result)
        dataframe["age"] = dataframe["age"].astype(int).astype(str)

        return dataframe

    @catch_sql_error
    def tasks_stats_by_space(self, filter_companies=[], filter_spaces=[]):
        session = self.db_connection.get_session()
        q = session.query(func.sum(Statistics.overdue), func.sum(Statistics.total), Statistics.stat_date). \
            join(User). \
            group_by(Statistics.stat_date)

        if filter_companies:
            q = q.filter(User.company.in_(filter_companies))

        if filter_spaces:
            q = q.filter(Statistics.space.in_(filter_spaces))

        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return pd.DataFrame(columns=['overdue', 'total', 'date'], data=list(q))

    @catch_sql_error
    def tasks_stats_by_user(self, filter_companies=[], filter_spaces=[], filter_overdue=False, filter_date=0):
        session = self.db_connection.get_session()

        company_stmt = ""
        space_stmt = ""
        where_stmt = ""
        overdue_stmt = ""
        date_stmt = ""

        # We're always interested in open tasks - never in done or disappeared tasks
        where_stmt = "WHERE tasks.is_done = 0"

        if filter_companies:
            company_stmt = "AND conf_users.company IN (" + ', '.join('"{}"'.format(t) for t in filter_companies) + ")"

        if filter_spaces:
            space_stmt = "AND pages.space IN (" + ', '.join('"{}"'.format(t) for t in filter_spaces) + ")"

        if filter_overdue:
            overdue_stmt = "AND tasks.reminder_date < DATE()"

        if filter_date == 2:
            date_stmt = "AND tasks.due_date IS NOT NULL"

        if filter_date == 1:
            date_stmt = "AND tasks.due_date IS NULL"

        stmt = f"""
         select total_sum.name, total, coalesce(overdue, 0) as overdue
       from (select conf_users.display_name as name, count(tasks.internal_id) as total
            from tasks join conf_users on conf_users.id = tasks.user_id
                join pages on pages.internal_id = tasks.page_link
                where tasks.is_done = 0
                {company_stmt} {space_stmt} {overdue_stmt} {date_stmt}
            group by conf_users.id) as total_sum
    left outer join (select conf_users.display_name as name, count(tasks.internal_id) as overdue
            from tasks join conf_users on conf_users.id = tasks.user_id
            JOIN pages ON pages.internal_id = tasks.page_link
            WHERE tasks.is_done = 0
              and julianday(tasks.due_date) < julianday(CURRENT_TIMESTAMP)
              {company_stmt} {space_stmt} {overdue_stmt} {date_stmt}
            GROUP BY conf_users.id) as overdue_sum
    on overdue_sum.name = total_sum.name
        """

        q = session.execute(stmt)

        result = list(q)
        logger.debug(f"returned {len(result)} entries. Statement was {stmt}")
        dataframe = pd.DataFrame(columns=['user', 'total', 'overdue'], data=result)
        return dataframe

    @catch_sql_error
    def tasks_by_age_and_space(self, filter_overdue=False, filter_date=0):
        ages = []
        spaces = []

        if filter_date in [0, 2]:
            if not filter_overdue:
                stmt = """select age, page_space from 
                        (SELECT round(julianday(CURRENT_TIMESTAMP) - julianday(tasks.reminder_date),0) AS age, 
                        pages.space AS page_space FROM tasks JOIN pages ON pages.internal_id = tasks.page_link 
                        WHERE tasks.is_done = 0 AND tasks.reminder_date IS NOT NULL) group by age
                        """
            else:
                stmt = """select age, page_space from 
                        (SELECT round(julianday(CURRENT_TIMESTAMP) - julianday(tasks.reminder_date),0) AS age, 
                        pages.space AS page_space FROM tasks JOIN pages ON pages.internal_id = tasks.page_link 
                        WHERE tasks.is_done = 0 AND tasks.reminder_date < DATE() AND tasks.reminder_date IS NOT NULL ) group by age
                        """
            session = self.db_connection.get_session()
            q = session.execute(stmt)
            result = list(q)
            logger.debug(f"returned {len(result)} entries. Statement was {stmt}")
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
        for x in bs.findAll("em"):
            x.unwrap()
        for x in bs.findAll("p"):
            text = x.text
            x.replaceWith(f"\n{text}")
        for x in bs.findAll("strong"):
            x.unwrap()
        for x in bs.findAll("img"):
            x.replaceWith("")
        for x in bs.findAll("span", attrs={"class": "placeholder-inline-tasks"}):
            x.unwrap()
        for x in bs.findAll("a", attrs={"class": "confluence-userlink"}):
            name = x.text
            x.replaceWith(name)
        for x in bs.findAll("a", attrs={"class": "jira-issue-key"}):
            name = x.text
            x.replaceWith(name)
        for x in bs.findAll("a"):
            name = x.text
            x.replaceWith(name)

        # Remove all further generic Spans.
        for x in bs.findAll("span"):
            x.unwrap()

        result = str(bs)

        replace_table = [
            ["<br/>", "  \n"],
            ["&gt;", ">"],
            ["&lt;", "<"],
            ["<p>", "  \n"],
            ["</p>", ""]
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
            join(User, Page).where(Page.internal_id == Task.page_link, User.id == Task.user_id,
                                   Task.is_done == False)

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

    def save_daily_statistics(self, date_of_statistics: date = date.today(), overwrite=False):
        """
        Will store statistical records in the database. Overdue and all tasks for today (or date given)
        per user and space.
        :param date_of_statistics: Date in statistics-table to be set
        :param overwrite: if there are values for this date already, shall we delete them first or add new ones?
        :return: True if success. False otherwise.
        """
        session = self.db_connection.get_session()
        if global_config.get_config("STATISTIC_DATE", optional=True):
            sql_date_of_statistics = global_config.get_config("STATISTIC_DATE", optional=False)
        else:
            sql_date_of_statistics = date_of_statistics.strftime("%Y-%m-%d")
        if overwrite:
            sql_string = f"delete from stats where stat_date = '{sql_date_of_statistics}'"
            x = session.execute(sql_string)
            session.commit()
            logger.info(f"{x.rowcount} stats records deleted for date {sql_date_of_statistics} from stats "
                        f"table because 'overwrite' was set to True.")
        sql_string = f"""
        insert into stats (stat_date, space, user_id, overdue, total)
            select "{sql_date_of_statistics}" as stat_date, x.space, x.user_id, y.overdue, x.total from (
                   select space, tasks.user_id, count(tasks.internal_id) as total 
                          from tasks join conf_users on tasks.user_id = conf_users.id 
                                     join pages on tasks.page_link = pages.internal_id 
                         group by conf_users.id, pages.space ) 
            as x left outer join (
                   select space, tasks.user_id, count(tasks.internal_id) as overdue 
                          from tasks 
                               join conf_users on tasks.user_id = conf_users.id 
                               join pages on tasks.page_link = pages.internal_id 
                         where tasks.due_date < CURRENT_DATE 
                    group by conf_users.id, pages.space ) 
            as y
            on x.user_id = y.user_id and x.space = y.space"""

        q = session.execute(sql_string)
        try:
            logger.info(f"{q.rowcount} statistics records written for date = {sql_date_of_statistics}.")
            session.commit()
            return True
        except Exception as ex:
            logger.warning(f"During stats-update received error {ex}")
            session.rollback()
            return False

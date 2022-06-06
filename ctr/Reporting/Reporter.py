from sqlalchemy import select

from ctr.Util import logger
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, User, Page
from sqlalchemy.sql import func
from sqlalchemy import distinct
from datetime import datetime
import pandas as pd


class UserReporting:
    def __init__(self, db_connection=SqlConnector):
        self.db_connection = db_connection
        self.session = self.db_connection.get_session()

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

    def get_spaces(self):
        stmt = distinct(Page.space)

        results = list(self.session.query(stmt))

        q = [row[0] for row in results]

        logger.debug(f"returned {len(q)} entries. Statement was: {str(q)}")
        return q


class TaskReporting:
    def __init__(self, db_connection: SqlConnector):
        self.db_connection = db_connection

    def task_count_by_space(self, filter_spaces, filter_overdue):
        session = self.db_connection.get_session()
        if not filter_overdue:
            date_to_filter = datetime.strptime("2199-12-31", "%Y-%m-%d")
        else:
            date_to_filter = datetime.now()
        if not filter_spaces or len("".join(filter_spaces)) == 0:
            q = session.query(func.count(Task.due_date), Page.space). \
                join(Page). \
                filter(Task.is_done == False,
                       Task.due_date < date_to_filter). \
                group_by(Page.space)
        else:
            q = session.query(func.count(Task.due_date), Page.space). \
                join(Page). \
                filter(Task.is_done == False,
                       Task.due_date < date_to_filter,
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
            filter(Task.is_done == False, Task.due_date < datetime.now()). \
            group_by(User.display_name)
        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return q

    def task_count_by_company(self, filter_companies, filter_overdue):
        session = self.db_connection.get_session()
        if not filter_overdue:
            date_to_filter = datetime.strptime("2199-12-31", "%Y-%m-%d")
        else:
            date_to_filter = datetime.now()
        if not filter_companies or len("".join(filter_companies)) == 0:
            q = session.query(func.count(Task.internal_id), User.company). \
                join(Task). \
                filter(Task.is_done == False,
                       Task.due_date < date_to_filter). \
                group_by(User.company)
        else:
            q = session.query(func.count(Task.internal_id), User.company). \
                join(Task). \
                filter(Task.is_done == False,
                       User.company.in_(filter_companies),
                       Task.due_date < date_to_filter). \
                group_by(User.company)

        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return pd.DataFrame(columns=['count', 'company'], data=list(q))

    def companies_from_users(self):
        session = self.db_connection.get_session()
        q = session.query(User.company).distinct()
        return pd.DataFrame(columns=["company"], data=list(q))

    def tasks_by_age_and_space(self, filter_overdue):
        if not filter_overdue:
            stmt = """select age, page_space from 
                    (SELECT round(julianday(CURRENT_TIMESTAMP) - julianday(tasks.due_date),0) AS age, 
                    pages.space AS page_space FROM tasks JOIN pages ON pages.internal_id = tasks.page_link 
                    WHERE tasks.is_done = 0 AND tasks.due_date) group by age
                    """
        else:
            stmt = """select age, page_space from 
                    (SELECT round(julianday(CURRENT_TIMESTAMP) - julianday(tasks.due_date),0) AS age, 
                    pages.space AS page_space FROM tasks JOIN pages ON pages.internal_id = tasks.page_link 
                    WHERE tasks.is_done = 0 AND tasks.due_date < DATE()) group by age
                    """
        session = self.db_connection.get_session()
        q = session.execute(stmt)
        # logger.debug(f"returned {len(list(q))} entries. Statement was {str(q)}")
        result = list(q)
        ages = []
        spaces = []
        for i in range(len(result)):
            ages.append(result[i][0])
            spaces.append(result[i][1])

        data = {"age": ages, "page_space": spaces}
        return pd.DataFrame(data)

    def get_task_view(self):
        session = self.db_connection.get_session()
        q = session.query(Task.internal_id, Task.task_description, Task.due_date,
                          Task.second_date,
                          User.display_name, Page.space, Page.page_name, Page.page_link, User.company). \
            join(User, Page).where(Page.internal_id == Task.page_link, User.id == Task.user_id, Task.is_done == True)

        logger.debug(f"returned {len(list(q))} entries. Statement was: {str(q)}")

        df = pd.DataFrame(columns=["task_internal_id", "Description", "Reminder", "Due",
                                   "Name", "Space", "page_name", "Page", "Company"],
                          data=list(q))
        # Convert from datetime-Format to date format
        df["Due"] = pd.to_datetime(df['Due']).dt.date
        df["Reminder"] = pd.to_datetime(df["Reminder"]).dt.date

        return df

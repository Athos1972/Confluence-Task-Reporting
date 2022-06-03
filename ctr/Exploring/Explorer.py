from sqlalchemy import distinct

from ctr.Util import logger
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, User, Page
from sqlalchemy.sql import update
import re
import pandas as pd

regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')

def get_company_name(email):
    if re.fullmatch(regex, email):
        return email.split("@")[1].split(".")[0]
    else:
        return "None"


class TaskExploring:
    def __init__(self, db_connection: SqlConnector):
        self.db_connection = db_connection
        self.session = self.db_connection.get_session()

    def get_spaces(self):
        stmt = distinct(Page.space)

        results = list(self.session.query(stmt))

        q = [row[0] for row in results]

        logger.debug(f"returned {len(q)} entries. Statement was: {str(q)}")
        return q

    def get_companies(self):
        stmt = distinct(User.company)

        results = list(self.session.query(stmt))

        q = [row[0] for row in results]

        logger.debug(f"returned {len(q)} entries. Statement was: {str(q)}")
        return q

    def init_user_companies(self):
        q = self.session.query(User.email, User.company)
        logger.debug(f"returned {len(list(q))} entries. Statement was: {str(q)}")

        for user in list(q):
            if user[1] is None:
                stmt = update(User).where(User.email == user[0]).values(company=get_company_name(user[0]))
                self.session.execute(stmt)
                self.session.commit()

    def get_task_view(self):
        q = self.session.query(Task.internal_id, Task.task_id, Task.task_description, Task.due_date, Task.second_date,
                               User.display_name, Page.space, Page.page_name, Page.page_link, User.company). \
            join(User, Page).where(Page.internal_id == Task.page_link, User.id == Task.user_id, Task.is_done == True)

        logger.debug(f"returned {len(list(q))} entries. Statement was: {str(q)}")

        return pd.DataFrame(columns=["task_internal_id", "task_id", "task_desc", "task_due_date", "task_second_date",
                                     "user_display_name", "page_space", "page_name", "page_link", "user_company"],
                            data=list(q))

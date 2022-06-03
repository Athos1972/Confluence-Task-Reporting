from ctr.Util import logger
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, User, Page
from sqlalchemy.sql import func
from datetime import datetime
import pandas as pd

class TaskReporting:
    def __init__(self, db_connection: SqlConnector):
        self.db_connection = db_connection
        self.session = self.db_connection.get_session()

    def task_count_by_space(self, company=None, space=None):
        q = self.session.query(func.count(Task.due_date), Page.space).\
            join(Page).\
            filter(Task.is_done == False).\
            group_by(Page.space)

        logger.debug(f"returned {q.count()} entries. Statement was: {str(q)}")
        return pd.DataFrame(columns=['count', 'space'], data=list(q))

    def task_overdue_count_by_space(self, company=None, space=None):
        q = self.session.query(func.count(Task.due_date), Page.space).\
            join(Page).\
            filter(Task.is_done == False, Task.due_date < datetime.now()).\
            group_by(Page.space)

        logger.debug(f"returned {q.count()} entries. Statement was: {str(q)}")

        return pd.DataFrame(columns=['count', 'space'], data=list(q))

    def task_open_count_by_user(self):
        q = self.session.query(User.display_name, func.count(Task.internal_id)).\
            join(Task).\
            filter(Task.is_done == False).\
            group_by(User.display_name)
        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return q

    def task_count_by_company(self):
        q = self.session.query(func.count(Task.internal_id), User.company).\
            join(Task).\
            filter(Task.is_done == False).\
            group_by(User.company)

        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return pd.DataFrame(columns=['count', 'company'], data=list(q))

    def task_overdue_count_by_company(self):
        q = self.session.query(func.count(Task.internal_id), User.company).\
            join(Task).\
            filter(Task.is_done==False, Task.due_date < datetime.now()).\
            group_by(User.company)

        logger.debug(f"returned {q.count()} entries. Statement was {str(q)}")
        return pd.DataFrame(columns=['count', 'company'], data=list(q))

    def tasks_by_age_and_space(self):
        stmt = """select age, count(age) as count_age, page_space from (SELECT julianday(CURRENT_TIMESTAMP) - julianday(tasks.due_date) AS age, 
page.space AS page_space FROM tasks JOIN page ON page.internal_id = tasks.page_link 
WHERE tasks.is_done = 0 AND tasks.due_date) group by age
        """
        q = self.session.execute(stmt)
        # logger.debug(f"returned {len(q)} entries. Statement was {str(q)}")
        return q


from sqlalchemy import select, distinct

from ctr.Util import logger
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, User, Page
from sqlalchemy.sql import func, text, update
from datetime import datetime
import re

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
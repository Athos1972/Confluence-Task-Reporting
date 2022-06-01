from sqlalchemy import select, distinct

from ctr.Util import logger
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, User, Page
from sqlalchemy.sql import func, text
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
        stmt = distinct(User.email)

        q = list(self.session.query(stmt))

        q = list(set([get_company_name(row[0]) for row in q]))

        logger.debug(f"returned {len(q)} entries. Statement was: {str(q)}")
        return q

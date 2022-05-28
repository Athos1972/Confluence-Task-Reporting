from atlassian import Confluence
from ctr.Util import global_config, logger
from os import environ
from datetime import datetime
import requests
import sys

from ctr.Database.connection import SqlConnector
from ctr.Database.model import User, Task
from sqlalchemy import update, insert


class Wrapper:
    def __init__(self, db_connection: SqlConnector = None):
        if not db_connection:
            self.db_connection = SqlConnector()
        else:
            self.db_connection = db_connection
        try:
            self.session = self.db_connection.get_session()
        except AttributeError as ex:
            logger.critical(f"Problem getting a Session. Problem: {ex}")
            sys.exit("Problem with session. Check logs or check .env-File, PYTHONPATH, etc.")


class UserWrapper(Wrapper):
    def __init__(self, confluence_name, confluence_userkey=None, email=None, display_name=None,
                 db_connection: SqlConnector = None):
        super().__init__(db_connection=db_connection)
        self.confluence_name = confluence_name
        self.confluence_userkey = confluence_userkey
        self.email = email
        self.display_name = display_name

    def update_user_in_database(self):
        found_user = self.session.query(User).filter(User.conf_name == self.confluence_name)
        if found_user.count() > 0:
            # User exists already in Database.
            found_user[0].last_crawled = datetime.now()
            logger.debug(f"user {found_user[0].conf_name} existed. Updated last_crawled-Timestamp")
            self.session.commit()
            return found_user[0].id
        else:
            new_user_for_database = User(conf_name=self.confluence_name,
                                         conf_userkey=self.confluence_userkey,
                                         email=self.email,
                                         display_name=self.display_name,
                                         last_crawled=datetime.now())
            logger.debug(f"User {self.confluence_name} newly added to database")
            self.session.add(new_user_for_database)
            self.session.commit()
            return new_user_for_database.id


class TaskWrapper(Wrapper):

    def __init__(self, username, global_id, due_date, second_date, page_link, db_connection: SqlConnector = None,
                 is_done: bool = False):
        super().__init__(db_connection=db_connection)
        self.username = username
        self.global_id = global_id
        self.due_date = due_date
        self.second_date = second_date
        self.is_done = is_done
        self.page_link = page_link

    def update_task_in_database(self):
        subquery_session = self.db_connection.get_session()
        found_task = self.session.query(Task).filter(Task.global_id == self.global_id)
        if found_task.count() > 0:
            # Task already exists.
            new_task = found_task[0]
        else:
            new_task = Task(self.global_id)
            self.session.add(new_task)

        new_task.due_date = self.due_date
        new_task.second_date = self.second_date
        new_task.is_done = self.is_done
        new_task.page_link = self.page_link
        new_task.user_id = subquery_session.query(User).filter(User.conf_name == self.username).first()

        self.session.commit()
        return new_task.internal_id


class CrawlConfluence:
    def __init__(self):
        self.instance = Confluence(url=global_config.get_config("CONF_BASE_URL"),
                                   username=environ.get("CONF_USER"),
                                   password=environ.get("CONF_PWD"))
        self.session = requests.Session()
        self.session.auth = (environ.get("CONF_USER"), environ.get("CONF_PWD"))
        self.confluence_url = global_config.get_config('CONF_BASE_URL', optional=False)

    def crawl_users(self, limit=10, max_entries=100, start=0):
        """

        :return:
        """
        url = f"{self.confluence_url}/rest/api/group/confluence-users/member"

        current_confluence_users = self.__repeated_get(url, limit=limit, max_entries=max_entries, start=start)

        for single_user in current_confluence_users:
            conf_details = self.read_userdetails_for_user(single_user["username"])
            for k, v in conf_details.items():
                single_user[k] = v

        return current_confluence_users

    def crawl_tasks_for_user(self, conf_user_name, limit=10, max_entries=100, start=0):
        """
        Holt via Confluence-API die Tasks zu einem User.

        # Unesaped schaut das wesentlich netter aus:
        # /rest/inlinetasks/1/my-task-report/?pageSize=500&pageIndex=0
        # &reportParameters=
        # {"columns":
        #   ["description","duedate","location"],
        #   "assignees":["netifu"],     <-- Der Confluence-User-Name
        #   "creators":[null],
        #   "status":"incomplete",
        #   "sortColumn":"duedate",
        #   "reverseSort":false
        # }
        # Escaped sieht es so aus:
        # /rest/inlinetasks/1/my-task-report/?pageSize=500&pageIndex=0&reportParameters=%7B%22
        # columns%22%3A%5B%22description%22%2C%22duedate%22%2C%22location%22%5D%2C%22assignees%22%3A%5B%22
        # netifu%22%5D%2C%22creators%22%3A%5Bnull%5D%2C%22status%22%3A%22incomplete%22%2C%22
        # sortColumn%22%3A%22duedate%22%2C%22reverseSort%22%3Afalse%7D

        :param conf_user_name:
        :param limit: Wie viele Ergebnisse je Call wollen wir abfragen?
        :param max_entries: Wie viele Ergebnisse gesamt?
        :param start: Ab welcher Zeile soll die Ausgabe starten
        :return:
        """

        url = f"{self.confluence_url}/rest/inlinetasks/1/my-task-report/?pageSize={limit}&pageIndex=0"
        url_append = f"&reportParameters=%7B%22columns%22%3A%5B%22description%22%2C%22duedate%22%2C%22location" \
                     f"%22%5D%2C%22assignees%22%3A%5B%22{conf_user_name}%22%5D%2C%22creators%22%3A%5Bnull%5D" \
                     f"%2C%22status%22%3A%22incomplete%22%2C%22sortColumn%22%3A%22duedate%22%2C%22" \
                     f"reverseSort%22%3Afalse%7D"

        task_list = self.__repeated_get(url=url, limit=limit, max_entries=max_entries, start=0, start_tag="pageIndex",
                                        limit_tag="pageSize", url_append=url_append)

        return task_list

    def __repeated_get(self, url, limit, max_entries, start=0, limit_tag="limit", start_tag="start",
                       url_append=None) -> list:
        results_found = []

        found_entries = True
        if not start:
            start = 0
        while found_entries:
            new_url = f'{url}?{limit_tag}={limit}&{start_tag}={start}{url_append}'
            response = self.session.get(new_url)

            results_found.extend(response.json().get("results"))

            start += limit
            if start >= max_entries:
                found_entries = False

            if response.status_code != 200:
                logger.debug(f"Statuscode: {response.status_code} für URL {new_url}")
                found_entries = False

        return results_found

    def read_userdetails_for_user(self, conf_username):
        result = self.session.get(f"{self.confluence_url}/rest/prototype/1/user/non-system/{conf_username}")
        # Dieser Aufruf funktioniert noch nicht in der Confluence-Server-Version
        # result = self.instance.get_user_details_by_username(username=conf_username,
        #                                                     expand='details.personal, details.business')
        # Das Ergebnis diesmal als HTML. E-Mail-Addresse ist zwischen <displayableEmail>Bernhard.Buhl@wienit.at</displayableEmail>
        return {"email": result.text[result.text.find("Email>") + 6:result.text.find("</displayableEmail>")]}
        return result

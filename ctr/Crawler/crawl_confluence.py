from atlassian import Confluence
from ctr.Util import global_config, logger, timeit
from os import environ
from datetime import datetime
from ctr.Util.Util import Util as UUtil
import requests
import sys
from bs4 import BeautifulSoup
from time import sleep

from ctr.Database.connection import SqlConnector
from ctr.Database.model import User, Task, Page


class Wrapper:
    def __init__(self, db_connection: SqlConnector = None):
        if not db_connection:
            self.db_connection = SqlConnector()
        else:
            self.db_connection = db_connection
        try:
            self.session = self.db_connection.get_session()
            self.session.autocommit = False
        except AttributeError as ex:
            logger.critical(f"Problem getting a Session. Problem: {ex}")
            sys.exit("Problem with session. Check logs or check .env-File, PYTHONPATH, etc.")
        self.crawl_confluence = None
        self.confluence_instance = None

    def _get_confuence_instance(self):
        if not self.confluence_instance:
            self.confluence_instance = Confluence(url=global_config.get_config("CONF_BASE_URL"),
                                                  username=environ.get("CONF_USER"),
                                                  password=environ.get("CONF_PWD"))

    def _get_confluence_crawler_instance(self):
        if not self.crawl_confluence:
            self.crawl_confluence = CrawlConfluence()


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

    def __init__(self, username, global_id, task_id, page_link, page_name, task_description, db_connection: SqlConnector = None,
                 is_done: bool = False, due_date=None):
        super().__init__(db_connection=db_connection)
        self.username = username
        self.global_id = global_id
        self.task_id = task_id
        self.due_date = due_date
        self.is_done = is_done
        self.page_link = page_link
        self.page_name = page_name
        self.task_description = task_description

    def update_task_in_database(self):
        subquery_session = self.db_connection.get_session()
        found_task = self.session.query(Task).filter(Task.global_id == self.global_id)
        if found_task.count() > 0:
            # Task already exists.
            logger.debug(f"Found entry {found_task[0].internal_id} with global_id = {self.global_id}")
            new_task = found_task[0]
        else:
            logger.debug(f"New task with global_id = {self.global_id}.")
            new_task = Task(self.global_id)
            new_task = self._add_pagelink_from_task(new_task, subquery_session)
            self.session.add(new_task)

        # These attributes may have changed since last crawl:
        new_task.due_date = self._convert_confluence_due_date_to_datetime(self.due_date)
        new_task.is_done = self.is_done
        new_task.task_description = self.task_description
        new_task.task_id = self.task_id
        new_task.last_crawled = datetime.now()

        new_task = self._derive_attributes_from_task_description(new_task)

        if new_task.is_done:
            logger.debug(f"Task {new_task} set to done.")

        if self.username:
            try:
                user = subquery_session.query(User).filter(User.conf_name == self.username).first()
                new_task.user_id = user.id
                user.tasks_last_crawled = datetime.now()
                subquery_session.commit()
            except AttributeError:  # User doesn't exist in Database?!
                logger.critical(f"User {self.username} does not exist in local database. Weird!")
                self.session.rollback()
                return None

        self.session.commit()
        return new_task.internal_id

    def _derive_attributes_from_task_description(self, new_task: Task):
        """
        Derive additional attributes of this task by parsing the HTML of the task description and parsing values.

        :param new_task: current status of new_task (with description filled)
        :return: Updated new_task
        """
        description_shortened = new_task.task_description

        if "\r" in description_shortened:
            description_shortened = description_shortened[:description_shortened.find("\r")]
        if "<br/>" in description_shortened:
            description_shortened = description_shortened[:description_shortened.find("<br/>")]
        if "<br />" in description_shortened:
            description_shortened = description_shortened[:description_shortened.find("<br />")]

        soup = BeautifulSoup(description_shortened, features="html.parser")
        new_task.second_date = self.__find_second_date_value_from_task_description(soup=soup)
        return new_task

    @staticmethod
    def __find_second_date_value_from_task_description(soup: BeautifulSoup):
        """
        Searches for second datetime-attribute in confluence (HTML)-Task
        :param soup:
        :return:
        """
        x = soup.find_all("time")
        if len(x) > 1:
            return datetime.strptime(x[1].attrs["datetime"], "%Y-%m-%d")
        return None

    def _add_pagelink_from_task(self, new_task, subquery_session):
        """
        the link looks like that: https://<conf-base-url>/display/<page_name>?focusedTaskId=xx
        or like that https://<conf_base_url>/viepage.action?pageId=<page_id>?focusedTaskId=xx

        We remove the ?focusedTaskId=xx from the url and search for that page in the databas. Add, if not there.
        Otherwise just set the remote-link to the Page entry into the Task-record

        :param new_task: Reference to Task-Instance
        :param subquery_session: Just a session
        :return:
        """
        self.page_link = self.page_link[:self.page_link.find("focusedTaskId=") - 1]
        new_task.page_link = subquery_session.query(Page).filter(
            Page.page_link == self.page_link).first()
        if not new_task.page_link:
            # If page-Entry doesn't exist yet let's create the page
            logger.debug(f"Page {self.page_name} was not in the database. Creating record.")
            page = Page(page_link=self.page_link,
                        page_name=self.page_name)
            page = self.get_space_from_pagelink(page)
            subquery_session.add(page)
            subquery_session.commit()
            new_task.page_link = page.internal_id
        else:
            new_task.page_link = new_task.page_link.internal_id
            logger.debug(f"Found page {new_task.page_link} existing in database")
        return new_task

    @timeit
    def get_space_from_pagelink(self, page: Page):
        """
        Searches in Confluence for further details of the page - namely the Space, that this page is stored in
        :param page: Page-Instance
        :return: nothing
        """

        if page.space:
            return

        if not self.confluence_instance:
            self._get_confuence_instance()

        if "viewpage.action" in page.page_link:
            # link looks like: <conf_base>/vieplage.action?pageId=<page_id>
            # check in other installations: This call looks to take at least twice as long as the call via requests
            # (in the else-Clause) even though we say "expand=None".
            page.page_id = page.page_link[page.page_link.find("=") + 1:]
            page_details = self.confluence_instance.get_page_by_id(page_id=page.page_id, expand=None)
            page.space = page_details["space"].get("key")
        else:
            # Here we should add a header-directive to session-object to only transmit the first 10000 characters
            self._get_confluence_crawler_instance()
            result = self.crawl_confluence.get_confluence_page_via_requests(page.page_link)
            # Get the unique page-id from HTML:
            page.page_id = self.__find_ajs_values_in_string("ajs-page-id", result.text)
            page.space = self.__find_ajs_values_in_string("ajs-space-key", result.text)

        return page

    @staticmethod
    def __find_ajs_values_in_string(search_string, base_string):
        """
        Extract values of ajs-xxx-yyyy-Fields in HTML-Header
        :param search_string: a string like ajs-space-key
        :param base_string: the response from the url-call (
        :return: the value of the requested field
        """
        search_string = f'"{search_string}" content="'
        start_pos = base_string.find(search_string) + len(search_string)
        end_pos = base_string.find('"', start_pos)
        return base_string[start_pos:end_pos]

    @staticmethod
    def _convert_confluence_due_date_to_datetime(confluence_date) -> datetime:
        """
        Confluence date comes as dd month year
        :param confluence_date:
        :return:
        """
        if isinstance(confluence_date, str):
            try:
                return datetime.strptime(confluence_date, "%d %b %Y")  # Month as abbrevation
            except ValueError:
                pass
            try:
                return datetime.strptime(confluence_date, "%d %B %Y")  # Month fully written
            except ValueError:
                pass
            try:
                return datetime.strptime(confluence_date, "%Y-%m-%d")  # 2022-05-25
            except ValueError:
                logger.critical(f"Dateformat unknown: {confluence_date}. Is it a date??")
                return None
        else:
            return confluence_date


class CrawlConfluence:
    def __init__(self):
        self.instance = Confluence(url=global_config.get_config("CONF_BASE_URL"),
                                   username=environ.get("CONF_USER"),
                                   password=environ.get("CONF_PWD"))
        self.session = requests.Session()
        self.session.auth = (environ.get("CONF_USER"), environ.get("CONF_PWD"))
        self.confluence_url = global_config.get_config('CONF_BASE_URL', optional=False)
        # In case you want to not strain system performance too much you can add sleep-duration in seconds in config
        self.sleep_between_tasks = global_config.get_config('sleep_between_crawl_tasks', default_value=0)

    def get_confluence_page_via_requests(self, page_name):
        """

        :param page_name:
        :return: Response from Session
        """
        sleep(self.sleep_between_tasks)
        return self.session.get(f'{self.confluence_url}/{page_name}')

    def crawl_users(self, limit=10, max_entries=100, start=0):
        """
        Get a List of Users from Confluence. Then read additional details for each user.
        :return: List of Confluence-Users as dict.
        """
        logger.debug(f"Starting to crawl max {max_entries} Users in slices of {limit}. Start from {start}")
        url = f"{self.confluence_url}/rest/api/group/confluence-users/member"

        current_confluence_users = self.__repeated_get(url, limit=limit, max_entries=max_entries, start=start)

        return current_confluence_users

    def recrawl_task(self, page_id, task_id):
        """
        All tries to work with https://developer.atlassian.com/cloud/confluence/rest/api-group-inline-tasks/#api-wiki-rest-api-inlinetasks-search-get
        and /rest/inlinetasks/1/task/ did not work out.
        # doesn't work: url = f"{self.confluence_url}/rest/inlinetasks/1/task/{page_id}/{task_id}"

        Reading the page, searching for the task-id and checking for status

        :param page_id:
        :param task_id:
        :return: is_done. True = done. False = still open
        """

        page = self.instance.get_page_by_id(page_id=page_id, expand="body.storage")
        sleep(self.sleep_between_tasks)
        logger.debug(f"Recrawling task {task_id} from page {global_config.get_config('CONF_BASE_URL')}"
                     f"/pages/viewpage.action?pageId={page_id}")
        soup = BeautifulSoup(page["body"]["storage"]["value"], features="html.parser")
        x = soup.find_all("ac:task")
        for y in x:
            l_id = int(y.find("ac:task-id").text)
            if l_id == task_id:
                # Return the task so that we can Map the result into the Task-ID
                return y
        logger.warning(f"Couldn't find Task-ID {task_id} in {page_id}. Setting task to completed")
        return False

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

        url = f"{self.confluence_url}/rest/inlinetasks/1/my-task-report/"
        url_append = f"&reportParameters=%7B%22columns%22%3A%5B%22description%22%2C%22duedate%22%2C%22location" \
                     f"%22%5D%2C%22assignees%22%3A%5B%22{conf_user_name}%22%5D%2C%22creators%22%3A%5Bnull%5D" \
                     f"%2C%22status%22%3A%22incomplete%22%2C%22sortColumn%22%3A%22duedate%22%2C%22" \
                     f"reverseSort%22%3Afalse%7D"
        logger.debug(f"Starting task-search for user {conf_user_name}.")

        task_list = self.__repeated_get(url=url, limit=limit, max_entries=max_entries, start=start,
                                        start_tag="pageIndex",
                                        limit_tag="pageSize",
                                        url_append=url_append)

        logger.debug(f"Found {len(task_list)} tasks for this user")

        return task_list

    def __repeated_get(self, url, limit, max_entries, start=0, limit_tag="limit", start_tag="start",
                       url_append="") -> list:
        """
        Reads from a paged URL until weither max_entries is reached or no more entries can be found.
        :param url: the base URL (without ?<limit_tag>=<limit>&<start_tag>=<start>
        :param limit: the number of records that are requested from the server
        :param max_entries: Up to how many records we should retrieve
        :param start: from which position (usually that would be 0!)
        :param limit_tag: what's the name of the limit-tag for this URL, e.g. limit, pageSize
        :param start_tag: what's the name of the start-tag for this URL, e.g. start, pageIndex
        :param url_append: any further parameters to be passed to the server (including leading "&"!)
        :return: List of gathered Response-Entries
        """
        results_found = []
        found_entries = True
        original_start_number = start
        retry_count = 0
        lJson = ""

        while found_entries:
            new_url = f'{url}?{limit_tag}={limit}&{start_tag}={start}{url_append}'

            if retry_count >= 4:
                logger.critical(f"Errors happened. Cant' catch url {new_url}. Aborting this crawl")
                found_entries=False
                continue

            try:
                response = self.session.get(new_url)
                sleep(self.sleep_between_tasks)
            except requests.HTTPError as ex:
                logger.debug(f"HTTP error  for URL {new_url}. retry_count = {retry_count}. Retrying...")
                retry_count += 1
                sleep(1)
                continue
            except requests.ConnectionError as ex:
                logger.debug(f"Connection error for URL {new_url}. retry_count = {retry_count}. Retrying...")
                retry_count += 1
                sleep(1)
                continue
            except requests.ReadTimeout:
                logger.debug(f"read-Timeout for URL {new_url}. retry_count = {retry_count}. Retrying...")
                sleep(1)
                retry_count += 1
                continue

            retry_count = 0

            if response.status_code < 300:
                lJson = response.json()
                # OK. That's a keen assumption but works so far: in the Respons there is only ONE List-Object. Calleer
                # is interested in all entries from this list-object.
                # E.g. when we call URL to list Users or Pages the name of the list (= "k") might be "Users" or "Pages"
                # while we find the list in "v". We add all entries from this list (usually dict's) to results_found
                for (k, v) in lJson.items():
                    if isinstance(v, list):
                        logger.debug(f"Received {len(v)} entries from server.")
                        results_found.extend(v)
                        if not v:
                            found_entries = False
                        break
            else:
                logger.critical(f"Error when reading url {new_url}. Error was: \n{response.text}")
                break

            start += limit
            if start >= (max_entries+original_start_number):
                # Exit when we received max_entries entries (+ Start-value ;-) )
                break

            if response.status_code != 200:
                logger.debug(f"Statuscode: {response.status_code} für URL {new_url} "
                             f"(most probably OK when we found all entries!)")
                break

        return results_found

    def read_userdetails_for_user(self, conf_username):
        try:
            result = self.session.get(f"{self.confluence_url}/rest/prototype/1/user/non-system/{conf_username}")
        except ConnectionError as ex:
            logger.error(f"Connection-Error during fetching user-details of user {conf_username}: {ex}")
            return {}
        # Dieser Aufruf funktioniert noch nicht in der Confluence-Server-Version
        # result = self.instance.get_user_details_by_username(username=conf_username,
        #                                                     expand='details.personal, details.business')
        # Das Ergebnis diesmal als HTML. E-Mail-Addresse ist zwischen
        # <displayableEmail>Bernhard.Buhl@wienit.at</displayableEmail>
        return {"email": result.text[result.text.find("Email>") + 6:result.text.find("</displayableEmail>")]}

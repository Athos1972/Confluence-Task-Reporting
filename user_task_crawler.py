"""
Crawles the tasks for users. When the program is started with parameter -OUWT = <any_value> the process happens
only for users who had previously had tasks. Otherwise all users (which were inserted/updated by user_crawler.py)
are processed
"""


from ctr.Util.Util import Util
from ctr.Util import global_config, logger
from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Crawler.crawl_confluence import TaskWrapper
from ctr.Database.connection import SqlConnector
from ctr.Database.model import User, Task
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import concurrent.futures


def set_users_tasks_to_done(user, l_subsession):
    """
    # First let's set all tasks to Completed. Like this we'll "uncomplete" still existing tasks without
    # having to recrawl tasks that are older
    :param user: User-Instance
    :param l_subsession: Database-Session
    """

    updated_records = l_subsession.execute(f"update Tasks set is_done = True where user_id = {user.id} "
                                         f"and is_done = False")
    l_subsession.commit()
    logger.info(f"Set {updated_records.rowcount} tasks of User {user.conf_name} to Done before we recrawl.")


def get_tasks_of_user(user, l_subsession):
    """
    Gets the tasks for this user from Confluence. Also sets tasks_last_crawled to current timestamp.
    :param user: User-Instance
    :param l_subsession: Database-Session
    :return:
    """
    user_tasks = crawler.crawl_tasks_for_user(user.conf_name, limit=limit, max_entries=max_entries_tasks, start=0)
    try:
        user.tasks_last_crawled = datetime.now()
    except AttributeError:
        # We're in the Query-Mode. In this mode we don't have a locked User-Instance, so we update manually:
        l_subsession.execute(f"update conf_users set tasks_last_crawled = CURRENT_TIMESTAMP "
                           f"where conf_users.id = {user.id}")
        l_subsession.commit()
    return user_tasks


def process_user(user):
    l_subsession = db_connection.get_session()
    set_users_tasks_to_done(user, l_subsession)
    tasks = get_tasks_of_user(user, l_subsession)
    for task in tasks:
        wrapper = TaskWrapper(
            db_connection=db_connection,
            username=user.conf_name, global_id=task['globalId'],
            page_link=task['pageUrl'],
            page_name=task['pageTitle'],
            task_id=task['taskId'],
            task_description=task['taskHtml'],
            is_done=task['taskCompleted'],
            reminder_date=task.get('dueDate'))
        wrapper.update_task_in_database()


if __name__ == '__main__':
    db_connection = SqlConnector()
    Util.load_env_file()
    crawler = CrawlConfluence()
    session = db_connection.get_session()
    limit = 20                     # page size
    max_entries_users = 5000
    max_entries_tasks = 900
    # Selektion of Users based on last_recrawled
    if global_config.get_config("OUWT", optional=False):
        q = session.query(User.conf_name, User.id, User.tasks_last_crawled, func.count(Task.task_id).
                          label("counted_tasks")).\
            join(Task).\
            filter(User.last_crawled > datetime.now() - timedelta(days=7)).\
            group_by(User.conf_name)
        # Only users who have tasks and do still exist in confluence. If we can't find them during crawling
        # users we don't set a new last_crawled date
    else:
        # All users which have been found within the last week (last_crawled) are selected
        q = session.query(User).filter(
            User.last_crawled > datetime.now() - timedelta(days=7)).limit(max_entries_users)
    # for debugging purposes: q = session.query(User).filter(User.conf_name == "NBUBEV")
    session.commit()
    logger.info(f"Executing Task Crawling for {len(list(q))} User-Records")

    current_hour = datetime.now().hour
    if 7 <= current_hour < 18:
        # Number of workers durcing the day
        num_workers = global_config.get_config("workers_during_daytime", optional=True, default_value = 5)
    else:
        # Number of workers during the night
        num_workers = global_config.get_config("workers_during_nighttime", optional=True, default_value = 15)

    # If the parameter to pause between activities is set to a value > 0 the workers will always be 1 assuming
    # that we want to fly under the radar of the confluence server
    if global_config.get_config("sleep_between_crawl_tasks", optional=True, default_value=0) > 0:
        num_workers = 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_user, user) for user in q]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error processing user: {e}")

    logger.info(f"Finished Task crawling for {len(list(q))} Users.")

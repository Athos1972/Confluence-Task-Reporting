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
from datetime import datetime


def set_users_tasks_to_done():
    # First let's set all tasks to Completed. Like this we'll "uncomplete" still existing tasks without
    # having to recrawl tasks that are older
    updated_records = subsession.execute(f"update Tasks set is_done = True where user_id = {user.id} "
                                         f"and is_done = False")
    subsession.commit()
    logger.info(f"Set {updated_records.rowcount} tasks of User {user.conf_name} to Done before we recrawl.")


def get_tasks_of_user(user_tasks):
    """
    Gets the tasks for this user from Confluence. Also sets tasks_last_crawled to current timestamp.
    :param user_tasks:
    :return:
    """
    user_tasks = crawler.crawl_tasks_for_user(user_tasks.conf_name, limit=limit, max_entries=max_entries_tasks, start=0)
    try:
        user_tasks.tasks_last_crawled = datetime.now()
    except AttributeError:
        # We're in the Query-Mode. In this mode we don't have a locked User-Instance, so we update manually:
        subsession.execute(f"update conf_users set tasks_last_crawled = CURRENT_TIMESTAMP "
                           f"where conf_users.id = {user_tasks.id}")
        subsession.commit()
    return user_tasks


if __name__ == '__main__':
    db_connection = SqlConnector()
    Util.load_env_file()
    crawler = CrawlConfluence()
    session = db_connection.get_session()
    subsession = db_connection.get_session()
    limit = 20                     # page size
    max_entries_users = 2000
    max_entries_tasks = 900
    # Selektion of Users based on last_recrawled
    if global_config.get_config("OUWT", optional=False):
        q = session.query(User.conf_name, User.id, User.tasks_last_crawled, func.count(Task.task_id).
                          label("counted_tasks")).\
            join(Task).\
            group_by(User.conf_name)
    else:
        q = session.query(User).order_by(User.tasks_last_crawled).limit(max_entries_users)
    # for debugging purposes: q = session.query(User).filter(User.conf_name == "NBUBEV")
    logger.info(f"Executing Task Crawling for {len(list(q))} User-Records")
    for user in q:
        set_users_tasks_to_done()
        tasks = get_tasks_of_user(user)
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
    session.commit()
    logger.info(f"Finished Task crawling for {len(list(q))} Users.")

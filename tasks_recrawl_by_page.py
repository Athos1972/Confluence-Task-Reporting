from ctr.Util.Util import Util
from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Crawler.crawl_confluence import TaskWrapper
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Page, Task, User
from sqlalchemy.sql import functions
from datetime import datetime
from ctr.Util import logger


if __name__ == '__main__':
    db_connection = SqlConnector()
    Util.load_env_file()
    crawler = CrawlConfluence()
    session = db_connection.get_session()
    subquerysession = db_connection.get_session()

    q = session.query(Page.page_id, Page.last_crawled, Page.page_name, Page.page_link, functions.count(Task.task_id))\
        .join(Task)\
        .where(Task.is_done == False)\
        .order_by(Page.last_crawled)

    for found_record in q:
        tasks_in_page = crawler.get_tasks_from_confluence_page(page_id=found_record.page_id)
        for single_task in tasks_in_page:
            time_element = single_task.find("time")
            if time_element:
                reminder_date = datetime.strptime(time_element.attrs["datetime"], "%Y-%m-%d").date()
            else:
                reminder_date = None
            task_id = int(str(single_task.find("ac:task-id").text))

            # Find confluence-Key of the first mentioned user_tasks.
            if "ri:userkey" not in str(single_task):
                logger.info(f"There is no mentioned user_tasks in this task-id {task_id} on page {found_record.page_id}. "
                            f"Ignoring Task: {str(single_task)}")
                continue

            user_conf_key = single_task.find("ri:user_tasks").attrs["ri:userkey"]
            user = subquerysession.query(User).where(User.conf_userkey==user_conf_key).first()
            if not user:
                logger.critical(f"In page {found_record.page_id} is task_id {task_id} with userkey "
                                f"{user_conf_key}. But can't seem to find this user_tasks in the database. When did you last"
                                f"recrawl users --> python user_crawler.py. "
                                f"Could also be a non-existing user_tasks (deleted).")
                continue

            # If the task (consisting of PageID and task-id) already existed let's pass the global_id. If it doesnt'
            # exist we'll have to have a dummy global_id
            global_id = subquerysession.query(Task.global_id).\
                where(Task.page_link == found_record.page_id,
                      Task.task_id==task_id).first()

            wrapper = TaskWrapper(db_connection=db_connection,
                                  username=user.conf_name,
                                  global_id=global_id,
                                  page_link=found_record.page_link,
                                  page_name=found_record.page_name,
                                  task_id=task_id,
                                  task_description=str(single_task),
                                  is_done=False if single_task.find("ac:task-status").text == "incomplete" else True,
                                  reminder_date=reminder_date)
            wrapper.update_task_in_database()


from ctr.Util.Util import Util
from ctr.Crawler.crawl_confluence import CrawlConfluence, TaskWrapper
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, Page, User
from datetime import datetime

if __name__ == '__main__':
    db_connection = SqlConnector()
    Util.load_env_file()
    crawler = CrawlConfluence()
    # Selektion von Usern basierend auf last_recrawled
    session = db_connection.get_session()
    q = session.query(Task.internal_id, Task.task_id, Task.is_done, User.conf_name, Page.page_id, Page.page_name)\
        .join(Page)\
        .join(User)\
        .filter(Task.due_date)\
        .order_by(Task.due_date)
    subquery_session = db_connection.get_session()

    for record in q:
        task = subquery_session.query(Task).filter(Task.internal_id == record.internal_id).first()
        soup = crawler.recrawl_task(page_id=record.page_id, task_id=record.task_id)
        if not soup:
            task.is_done = True
        else:
            time_element = soup.find("time")
            if time_element:
                due_date = datetime.strptime(time_element.attrs["datetime"], "%Y-%m-%d")
            else:
                due_date = None
            wrapper = TaskWrapper(username=record.conf_name,
                                  global_id=task.global_id,
                                  page_link=task.page_link,
                                  page_name=record.page_name,
                                  task_id=task.task_id,
                                  task_description=str(soup),
                                  is_done=True if soup.find("ac:task-status").text == "incomplete" else False,
                                  due_date=due_date)
            wrapper.update_task_in_database()

        subquery_session.commit()

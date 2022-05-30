from ctr.Util.Util import Util
from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Crawler.crawl_confluence import TaskWrapper
from ctr.Database.connection import SqlConnector
from ctr.Database.model import User
from sqlalchemy import desc

if __name__ == '__main__':
    db_connection = SqlConnector()
    Util.load_env_file()
    crawler = CrawlConfluence()
    # Selektion von Usern basierend auf last_recrawled
    session = db_connection.get_session()
    limit = 1
    # q = session.query(User).order_by(desc(User.last_crawled)).limit(limit)
    q = session.query(User).filter(User.conf_name == "NBUBEV")
    for user in q:
        tasks = crawler.crawl_tasks_for_user(user.conf_name, limit=50, max_entries=200, start=0)
        for task in tasks:
            wrapper = TaskWrapper(username=user.conf_name, global_id=task['globalId'],
                                  page_link=task['pageUrl'],
                                  page_name=task['pageTitle'],
                                  task_id=task['taskId'],
                                  task_description=task['taskHtml'],
                                  is_done=task['taskCompleted'],
                                  due_date=task['dueDate'])

            wrapper.update_task_in_database()

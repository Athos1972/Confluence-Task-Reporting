from ctr.Util.Util import Util
from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Database.connection import SqlConnector
from ctr.Database.model import Task, Page
from datetime import datetime

if __name__ == '__main__':
    db_connection = SqlConnector()
    Util.load_env_file()
    crawler = CrawlConfluence()
    # Selektion von Usern basierend auf last_recrawled
    session = db_connection.get_session()
    q = session.query(Task.internal_id, Task.task_id, Task.is_done, Page.page_id).join(Page).order_by(Task.due_date)
    subquery_session = db_connection.get_session()

    for record in q:
        task = subquery_session.query(Task).filter(Task.internal_id == record.internal_id).first()
        task.is_done = crawler.recrawl_task(page_id = record.page_id, task_id=record.task_id)
        task.last_crawled = datetime.now()
        subquery_session.commit()
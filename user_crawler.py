from ctr.Util.Util import Util
from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Crawler.crawl_confluence import UserWrapper
from ctr.Database.connection import SqlConnector
from random import randint

if __name__ == '__main__':
    db_connection = SqlConnector()
    Util.load_env_file()
    crawler = CrawlConfluence()
    start = randint(1, 1500)
    max_entries = 20
    conf_users = crawler.crawl_users(limit=10, max_entries=max_entries, start=start)
    for conf_user in conf_users:
        new_user = UserWrapper(confluence_name=conf_user.get('username'),
                               confluence_userkey=conf_user.get('userKey'),
                               display_name=conf_user.get("displayName"),
                               email=conf_user.get("email"),
                               db_connection=db_connection)
        user_id = new_user.update_user_in_database()
    print(f"{len(conf_users)} verarbeitet (von {start} bis {start + max_entries})")

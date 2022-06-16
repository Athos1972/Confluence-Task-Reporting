"""
Gets all users from conflunce installation and stores them in the database. E-Mail, which can't be received from the API
is read from user_tasks profile page if user_tasks was not there already.
"""
from ctr.Util.Util import Util
from ctr.Util import logger
from ctr.Crawler.crawl_confluence import CrawlConfluence
from ctr.Crawler.crawl_confluence import UserWrapper
from ctr.Database.connection import SqlConnector
from ctr.Database.model import User

if __name__ == '__main__':
    db_connection = SqlConnector()
    session = db_connection.get_session()
    Util.load_env_file()
    crawler = CrawlConfluence()
    start = 0
    max_entries = 2000
    new_users = []
    conf_users = crawler.crawl_users(limit=50, max_entries=max_entries, start=start)
    for conf_user in conf_users:
        q = session.query(User).filter(User.conf_name == conf_user.get('username')).first()
        if not q or not "@" in q.email:
            if not q:
                new_users.append(conf_user)
            # Attributes like E-Mail-Address are not expandable/received in the member-API-Call, so we must call
            # again (this time for each user_tasks) to receive those details.
            # As this data tends to be static don't do this during each crawl.
            logger.debug(f"Getting further details for user_tasks {conf_user['username']}")
            conf_details = crawler.read_userdetails_for_user(conf_user["username"])
            for k, v in conf_details.items():
                conf_user[k] = v

        new_user = UserWrapper(confluence_name=conf_user.get('username'),
                               confluence_userkey=conf_user.get('userKey'),
                               display_name=conf_user.get("displayName"),
                               email=conf_user.get("email"),
                               db_connection=db_connection)
        user_id = new_user.update_user_in_database()
    print(f"{len(conf_users)} User (re)crawled from Confluence (from {start} to {start + len(conf_users)}). "
          f"{len(new_users)} added to database.")
    for new_user in new_users:
        print(f"Username: {new_user.get('username')}, Name: {new_user.get('displayName')}, "
              f"E-Mail: {new_user.get('email')}")

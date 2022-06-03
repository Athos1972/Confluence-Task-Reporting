from ctr.Util.Util import Util
from ctr.Util import global_config
from ctr.Database.connection import SqlConnector
from ctr.Database.model import CreateTableStructures
from ctr.Database.model import User, Task, Page
from datetime import datetime, timedelta
from random import choices
from faker import Faker
import string
from random import choices, randint
from pathlib import Path
from ctr.Crawler.crawl_confluence import TaskWrapper

# Empties testdatabase, creates 1500 random users, 1500 Confluence-Pages and 3000 Tasks for those users on those
# pages

Util.load_env_file()
db_connection = SqlConnector(file=f"sqlite:///{Path.cwd().joinpath('testdatabase.db')}")
session = db_connection.get_session()

faker = Faker(locale="en_US")

print("clearing testdatabase")
session.execute("delete from tasks")
session.execute("delete from pages")
session.execute("delete from conf_users")

print("Creating Users")
for i in range(1501):
    user = User(conf_name=f"NBU{i}",
                conf_userkey="".join(choices(string.ascii_letters, k=22)),
                email = faker.email(),
                display_name=faker.name())
    session.add(user)
    session.commit()

space_list = [
    "Project 47",
    "Project 2",
    "Project 1",
    "MyProject"
]

print("creating pages")
for i in range(1501):
    page = Page(page_link=f"/viewpage.action?pageId={randint(900000,1100000)}",
                page_name=faker.sentence(nb_words=randint(5,10)))
    page.space = space_list[randint(0,3)]
    page.page_id = randint(9000000,11000000)
    session.add(page)
    session.commit()

print("Creating Pages")
for i in range(3000):
    q = session.query(Page).filter(Page.internal_id==randint(0,1500)).first()
    if not q:
        continue
    taskwrapper = TaskWrapper(db_connection=db_connection,
                              username=str(session.query(User.conf_name).filter(User.id==randint(0,1500)).first()[0]),
                              global_id=i,
                              task_id = randint(1,50),
                              task_description=faker.sentence(nb_words=randint(2,12)),
                              page_link=q.page_link,
                              page_name=q.page_name,
                              is_done=True if randint(1,100) %2 == 0 else False
                              )
    taskwrapper.update_task_in_database()
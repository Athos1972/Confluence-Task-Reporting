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
import datetime

# Empties testdatabase, creates 1500 random users, 1500 Confluence-Pages and 3000 Tasks for those users on those
# pages

db_connection = SqlConnector(file=f"sqlite:///{Path.cwd().joinpath('prod.db')}")
session = db_connection.get_session()

faker = Faker(locale="en_US")

print("clearing database")
session.execute("delete from tasks")
session.execute("delete from page")
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
    page.space = space_list[randint(0, 3)]
    page.page_id = randint(9000000, 11000000)
    session.add(page)
    session.commit()

print("Creating tasks")
for i in range(3000):
    q = session.query(Page).filter(Page.internal_id == randint(0, 1500)).first()

    p = session.query(User).filter(User.id == randint(0, 1500)).first()

    task = Task(
        global_id=i,
    )
    task.task_id = randint(1, 50)
    task.task_description = faker.sentence(nb_words=randint(2, 12))
    task.page_link = q.page_link
    task.page_name = q.page_name
    task.is_done = True if randint(1, 100) % 2 == 0 else False
    if p:
        task.user_id = p.id
    task.due_date = datetime.datetime(randint(2020, 2024), randint(1, 12), randint(1, 26))

    session.add(task)
    session.commit()
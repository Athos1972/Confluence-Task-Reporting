import os
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

from ctr.Database.connection import SqlConnector
from ctr.Database.model import User, Task, Page, Statistics
from datetime import date, timedelta
from faker import Faker
import string
from random import choices, randint
from pathlib import Path

# Empties testdatabase, creates 1500 random users, 1500 Confluence-Pages and 3000 Tasks for those users on those
# pages

db_connection = SqlConnector(file=f"sqlite:///{Path.cwd().joinpath('testdatabase.db')}")
session = db_connection.get_session()

faker = Faker(locale="en_US")

print("clearing database")
session.execute("delete from tasks")
session.execute("delete from pages")
session.execute("delete from conf_users")
session.execute("delete from stats")

print("Creating Users")

company_list = [
    "siemens",
    "ibm",
    "sap",
]

for i in range(1501):
    company = company_list[randint(0, len(company_list) - 1)]
    user = User(
        conf_name=f"NBU{i}",
        conf_userkey="".join(choices(string.ascii_letters, k=22)),
        email=faker.email().replace("example", company),
        company=company,
        display_name=faker.name())
    session.add(user)
session.commit()

space_list = [
    "New Forms",
    "Operations",
    "New OS",
    "New Mobility",
    "MyProject"
]

print("creating pages")
for i in range(1501):
    page = Page(page_link=f"/viewpage.action?pageId={randint(900000, 1100000)}",
                page_name=faker.sentence(nb_words=randint(5, 10)))
    page.space = space_list[randint(0, len(space_list) - 1)]
    page.page_id = randint(9000000, 11000000)
    session.add(page)
session.commit()

print("Creating tasks")
for i in range(3000):
    page_link = randint(0, 1500)
    p = session.query(User).filter(User.id == randint(0, 1500)).first()
    task = Task(
        global_id=i,
    )
    task.task_id = randint(1, 50)
    task.task_description = faker.sentence(nb_words=randint(2, 12))
    task.page_link = page_link
    task.page_name = "page_name"
    task.is_done = True if randint(1, 100) % 2 == 0 else False
    if p:
        task.user_id = p.id
    task.reminder_date = date(year=randint(2020, 2024), month=randint(1, 12), day=randint(1, 26))
    if i % 3 == 0:
        task.second_date = date(year=randint(2020, 2024), month=randint(1, 12), day=randint(1, 26))
    if i % 6 == 0:
        task.reminder_date = None
        task.second_date = None
        task.due_date = None

    session.add(task)
session.commit()

print("creating stats")
start_date = date(year=randint(2020, 2024), month=randint(1, 12), day=randint(1, 26))
# Statistics data will be collected every day. Here for instance for 2 months:
for i in range(60):
    current_date = start_date + timedelta(days=i)
    # Dummy Users - some days many of them have overdue/tasks, some days less
    for n in range(randint(200, 300)):
        stat = Statistics(space=space_list[randint(0, len(space_list) - 1)],
                          date=current_date,
                          user_id=n,
                          overdue=randint(0, 15),
                          total=randint(15, 30))
        session.add(stat)

session.commit()

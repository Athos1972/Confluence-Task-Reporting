from ctr.Reporting.Reporter import TaskReporting
from ctr.Database.connection import SqlConnector
from ctr.Util.Util import Util
from ctr.Util import global_config, timeit
from datetime import datetime, date
import pandas as pd
import numpy as np


@timeit
def execute():
    def calculate_days(due_date):
        if pd.isna(due_date):
            return 0
        today = pd.Timestamp(date.today())
        try:
            diff = (today - pd.Timestamp(due_date)).days
            return diff
        except OverflowError:
            # Handle the case where date difference is too large
            return 0

    # Apply the function to each date in the 'Due_DT' column
    db_connection = SqlConnector()
    Util.load_env_file()
    reporter = TaskReporting(db_connection=db_connection)
    df = reporter.get_tasks_view()
    # If we were started with CLI-Parameter = "OO" then we want only overdue values
    if global_config.get_config("ONLY_OVERDUE", default_value=False):
        df = df.drop(df[df["Due"] < date.today()].index)

    df = df.drop(['task_internal_id'], axis=1)

    # Nur auf unsere Spaces filtern
    allowed_values = ["PRGWgS4H", "iniPFM76", "S4SC"]
    df = df[df['Space'].isin(allowed_values)]
    # Convert 'Due' to datetime and extract date
    df['Due_DT'] = pd.to_datetime(df['Due'], errors='coerce').dt.date
    # Calculate the difference in days
    df['DueDiff'] = df['Due_DT'].apply(calculate_days)

    # DueDate nur für Zukunft im Export betrachten
    df = df[df['DueDiff'] > 0]

    # Temporäre Spalte wieder killen
    df.drop('Due_DT', axis=1, inplace=True)

    file_name = f"task_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    sheetname = "Confluence-Tasks"

    Util.write_pd_to_excel(file_name=file_name, sheetname=sheetname, dataframe=df)
    print(f"File {file_name} created.")


if __name__ == '__main__':
    execute()

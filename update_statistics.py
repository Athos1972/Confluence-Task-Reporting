"""
Gets all users from conflunce installation and stores them in the database. E-Mail, which can't be received from the API
is read from user_tasks profile page if user_tasks was not there already.
"""
from ctr.Util.Util import Util
from ctr.Util import logFilename, global_config
from ctr.Database.connection import SqlConnector
from ctr.Reporting.Reporter import TaskReporting


if __name__ == '__main__':
    db_connection = SqlConnector()
    Util.load_env_file()
    task_reporter = TaskReporting(db_connection=db_connection)
    y = task_reporter.save_daily_statistics(overwrite=True)
    if y:
        print(f"Statistical data for today saved")
    else:
        print(f"Something happened during execution of update_statistics. Please check logfile {logFilename}")

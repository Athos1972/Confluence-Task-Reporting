"""
Provides the logger and global_config-Variables to all classes, programs, etc.
"""
import logging
from pathlib import Path
from datetime import datetime
from ctr.Util.Config import Config
import time
import urllib3

urllib3.disable_warnings()    # sollte die dämlichen SSL-Warnings in der JIRA-Test-Maschine supressen

# Globale Variable
global_config = Config()

if global_config.get_config("log_dir"):
    base_path = Path(global_config.get_config("log_dir"))
    base_path.mkdir(parents=True, exist_ok=True)
else:
    base_path = Path.cwd()
logFilename = base_path.joinpath(datetime.now().strftime("%Y%m%d_%H%M%S") + '.log')
print(f"Logfile used: {logFilename}")

# Bit more advanced logging
logger = logging.getLogger(global_config.get_config("logger_name", optional=False))
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fileHandler = logging.FileHandler(logFilename, encoding="UTF-8")
fileHandler.setLevel(level=logging.DEBUG)
# create console handler with a higher log level
channelHandler = logging.StreamHandler()
channelHandler.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s _ %(levelname)s _ %(module)s _ %(funcName)s : %(message)s')
channelHandler.setFormatter(formatter)
fileHandler.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(channelHandler)
logger.addHandler(fileHandler)


def timeit(f):
    """
    timeit-decorator
    :param f:
    :return:
    """

    def timed(*args, **kw):

        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        logger.info(f'func: {f.__name__} args:[{args}, {kw}] took: {te-ts:.5} sec')
        return result

    return timed

import logging
import os
from datetime import datetime
import argparse

# Init arguments
try:
    from modules.utils import arg_parser
except ImportError:
    arg_parser = argparse.ArgumentParser()

arg_parser.add_argument('-d', '--debug', action='store_true',  default=False,
                    help='set debug for console channel')

args = arg_parser.parse_known_args()
# args = arg_parser.parse_args()

if args[0].debug:
    console_level = logging.DEBUG
else:
    console_level = logging.INFO

# Date strings
datetime_now = datetime.now() # Today date
date_now_str = datetime_now.strftime("%Y-%m-%d") # String with only date
datetime_now_str = datetime_now.strftime("%Y-%m-%d_%H-%M-%S") # String with date and time

log_format="[%(asctime)s]:[%(threadName)s]:[%(name)s]:%(levelname)s:%(message)s"


package_directory = os.path.dirname(os.path.abspath(__file__))
log_dir = f'{package_directory}/../logs/{date_now_str}'
log_error_dir = f'{package_directory}/../logs/{date_now_str}/errors'
os.makedirs(log_dir, exist_ok=True) # Create log dir
os.makedirs(log_error_dir, exist_ok=True) # Create log error dir

log_file = f'{log_dir}/{datetime_now_str}.log'
log_error_file = f'{log_error_dir}/{datetime_now_str}.log'
formatter = logging.Formatter(log_format)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler() # Logs to console
ch.setLevel(console_level)
ch.setFormatter(formatter)

fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')  # Logs to file
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

eh = logging.FileHandler(log_error_file, mode='w', encoding='utf-8', delay=True)  # Logs errors only to file
eh.setLevel(logging.ERROR)
eh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)
logger.addHandler(eh)

logger.debug(f"{'#'*50}")
logger.debug(f"{f' {datetime_now_str} ':#^50}")

logger.info("Completed init logging")
if console_level == logging.DEBUG: logger.debug("Debug mode for console")

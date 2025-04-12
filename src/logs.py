import json
import logging
from typing import Literal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def fancy_print(data, log_level=logging.INFO):
    log_function = {
        logging.DEBUG: logger.debug,
        logging.INFO: logger.info,
        logging.WARNING: logger.warning,
        logging.ERROR: logger.error,
        logging.CRITICAL: logger.critical
    }.get(log_level, logger.info)
    
    log_function(json.dumps(data, indent=2, separators=(',', ': ')))

def log_debug(data):
    fancy_print(data, log_level=logging.DEBUG)

def log_info(data):
    fancy_print(data, log_level=logging.INFO)

def log_warning(data):
    fancy_print(data, log_level=logging.WARNING)

def log_error(data):
    fancy_print(data, log_level=logging.ERROR)

def log_critical(data):
    fancy_print(data, log_level=logging.CRITICAL)

def log_exception(data):
    fancy_print(data, log_level=logging.ERROR)

def log_exception_with_traceback(data):
    import traceback
    log_exception(data)
    logger.error(traceback.format_exc())
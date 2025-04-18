import json
import logging

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

def _fancy_print(data, log_level=logging.INFO):
    log_function = {
        logging.DEBUG: logger.debug,
        logging.INFO: logger.info,
        logging.WARNING: logger.warning,
        logging.ERROR: logger.error,
        logging.CRITICAL: logger.critical
    }.get(log_level, logger.info)
    
    try:
        log = json.dumps(data, indent=2, separators=(',', ': '))
    except (TypeError, ValueError):
        log = str(data)
    
    log_function(log)

def log_debug(data):
    _fancy_print(data, log_level=logging.DEBUG)

def log_info(data):
    _fancy_print(data, log_level=logging.INFO)

def log_warning(data):
    _fancy_print(data, log_level=logging.WARNING)

def log_error(data):
    _fancy_print(data, log_level=logging.ERROR)

def log_critical(data):
    _fancy_print(data, log_level=logging.CRITICAL)

def log_exception(data):
    _fancy_print(data, log_level=logging.ERROR)

def log_exception_with_traceback(data):
    import traceback
    log_exception(data)
    logger.error(traceback.format_exc())
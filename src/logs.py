import sys

import logging
from src import constants

# Create a custom logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

log_prefix = '%(filename)20s:%(lineno)4s - %(funcName)20s()'

# - Create handlers
# Console log
c_handler = logging.StreamHandler()
c_handler.setLevel(getattr(logging, constants.LOG_LEVEL))
c_format = logging.Formatter(f'[{log_prefix}] - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)

# File
f_handler = logging.FileHandler(constants.LOG_FILE)
f_handler.setLevel(getattr(logging, constants.LOG_LEVEL_FILE))
f_format = logging.Formatter(f'%(asctime)s > [%(process)7d - {log_prefix}] [%(levelname)s]: %(message)s',
                             '%d-%b-%y %H:%M:%S')
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

logger.info('App started!')


# logger.debug('This is debug!')
# logger.warning('This is a warning')
# logger.error('This is an error')
# logger.info('This is info!')
# logger.critical('This is critical!')

# Handle uncaught exceptions
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

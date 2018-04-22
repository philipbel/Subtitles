import logging
import sys

logger = logging.getLogger('SubFinder')


def init():
    # TODO: Make configurable
    logger.setLevel(logging.DEBUG)
    # TODO: Create a file handler and log to a file
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s %(levelname)s %(thread)x] "
        "%(filename)s:%(lineno)d:%(funcName)s: %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

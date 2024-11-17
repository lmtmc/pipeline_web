import logging
import sys


def setup_logger():
    # create logger
    logger = logging.getLogger('app')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    c_handler = logging.StreamHandler(sys.stdout)
    f_handler = logging.FileHandler('app.log')
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.DEBUG)

    # create formatter
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # add handlers to logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger


logger = setup_logger()

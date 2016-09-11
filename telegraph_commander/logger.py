import logging


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger


def get_console_handler():
    log_stream_handler = logging.StreamHandler()
    log_stream_handler.setLevel(logging.DEBUG)
    formater = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s] - %(message)s")
    log_stream_handler.setFormatter(formater)
    return log_stream_handler
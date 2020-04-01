"""
Module that provides logging functions for any other module and adapts to any environment where it is running.
"""
import logging

from app.config import RUN_CONFIG

DEBUG = 'DEBUG'
INFO = 'INFO'
WARNING = 'WARNING'
ERROR = 'ERROR'
CRITICAL = 'CRITICAL'


def debug(msg):
    """
    Logs a debug message
    """
    log_msg(DEBUG, msg)

def info(msg):
    """
    Logs an info message
    """
    log_msg(INFO, msg)

def warning(msg):
    """
    Logs a warning message
    """
    log_msg(WARNING, msg)

def error(msg):
    """
    Logs an error message
    """
    log_msg(ERROR, msg)

def critical(msg):
    """
    Logs a critical message
    """
    log_msg(CRITICAL, msg)

def log_msg(level, msg):
    """
    Prints a message to the console
    """
    logger = RUN_CONFIG.get('logger')
    if logger is None:
        print(level, ':', msg)
    else:
        gunicorn_logger = logging.getLogger(logger)

        if level == DEBUG:
            gunicorn_logger.debug(msg)
        elif level == INFO:
            gunicorn_logger.info(msg)
        elif level == WARNING:
            gunicorn_logger.warning(msg)
        elif level == ERROR:
            gunicorn_logger.error(msg)
        elif level == CRITICAL:
            gunicorn_logger.critical(msg)


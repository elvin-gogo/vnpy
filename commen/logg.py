import logging
import os
import os.path
import sys
from logging.handlers import TimedRotatingFileHandler
import json

fmt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
smt = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'


is_debug = False


def _init_log(app='vnpy'):
    log_file = os.path.join("/Users/zhangchao/ByteTrade", app, 'vnpy.log')
    if not os.path.exists(os.path.dirname(log_file)):
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    print('log file', log_file)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if is_debug else logging.INFO)

    handler = TimedRotatingFileHandler(log_file,
                                       when='d',
                                       interval=1,
                                       backupCount=3)
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if is_debug else logging.INFO)
    formatter = logging.Formatter(smt)
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


_root_logger = None


def get_logger(app='vnpy'):
    global _root_logger
    if _root_logger is None:
        _root_logger = _init_log(app)
    return _root_logger


if __name__ == '__main__':
    get_logger()

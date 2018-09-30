# 设置logging
def getLog(name=''):
    import os
    import logging.config
    curDir = os.path.dirname(__file__)
    logging.config.fileConfig(curDir + '/../cfg/log.conf')
    return logging.getLogger(name)
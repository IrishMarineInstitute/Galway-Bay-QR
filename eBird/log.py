import logging
def set_logger():
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='/log/app.log', 
                        format='%(message)s',
                        level=logging.INFO)
    return logger

from datetime import datetime
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

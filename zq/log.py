from loguru import logger as log
from zq.config import settings
log.add(level=settings.LOG_LEVEL)
log.add("file_{time}.log", rotation="500 MB")
log.add("file_{time}.log", rotation="12:00")
log.add("file_{time}.log", rotation="1 week")
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file: str = "app.log", level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Rotating handle - caps file size, keeps backups

    handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024, # 5 MB per file
        backupCount=3             # keeps app.log, app.log.1, app.log.2, app.log.3
    )
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

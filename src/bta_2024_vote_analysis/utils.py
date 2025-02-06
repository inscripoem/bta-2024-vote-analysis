import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"

def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)]
    )

    return logging.getLogger(name)

from pathlib import Path
import logging.config


BASE_DIR = Path(__file__).resolve().parent.parent


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "log.log",
            "formatter": "simple",
            "encoding": "utf-8"
        }
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": True,
        },
        "file": {
            "level": "INFO",
            "handlers": ['file'],
            "propagate": True,
        },
        "full_log": {
            "level": "INFO",
            "handlers": ['console', 'file'],
            "propagate": True,
        }
    },
    "formatters": {
        "verbose": {
            "format": "{name} {levelname} {asctime} {module} {lineno} {funcName} {message} ",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
        "simple2": {
            "format": "[{levelname:^11}] {asctime} {message}",
            "style": "{",
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

try:
    logging.config.dictConfig(LOGGING_CONFIG)
except ValueError:
    pass


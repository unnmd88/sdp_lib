import logging.config


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "log.log",
            "formatter": "verbose2",
        },
        "file2": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "reduce_log.log",
            "formatter": "verbose2",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": True,
        },
        "full_log": {
            "level": "INFO",
            "handlers": ['file'],
            "propagate": True,
        },
        "reduce_log": {
            "level": "INFO",
            "handlers": ['file2'],
            "propagate": True,
        }
    },
    "formatters": {
        "verbose": {
            # "format": "{name} {levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "format": "{name} {levelname} {asctime} {module} {lineno} {funcName} {message} ",
            "style": "{",
        },
        "verbose2": {
            # "format": "{name} {levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "format": "{name} [{levelname:^11}] {asctime} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)


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
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "log.log",
            "formatter": "verbose",
        },
        "trap_verbose_file_handler": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "verbose_traps.log",
            "formatter": "verbose_trap",
        },
        "trap_common_file_handler": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "common_traps.log",
            "formatter": "verbose_trap",
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
        "trap_verbose": {
            "level": "INFO",
            "handlers": ['trap_verbose_file_handler'],
            "propagate": True,
        },
        "trap_common": {
            "level": "INFO",
            "handlers": ['trap_common_file_handler'],
            "propagate": True,
        }
    },
    "formatters": {
        "verbose": {
            "format": "{name} {levelname} {asctime} {module} {lineno} {funcName} {message} ",
            "style": "{",
        },
        "verbose_trap": {
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


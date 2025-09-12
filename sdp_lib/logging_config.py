from pathlib import Path
import logging.config


BASE_DIR = Path(__file__).resolve().parent.parent


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/log.log",
            "formatter": "verbose",
        },
        "file2": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/penetrate_stage.log",
            "formatter": "simple2",
        },
        "file_in_cwd": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": "log_passport.log",
            "formatter": "simple2",
        },
        "server": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "server_ntfc.log",
            "formatter": "verbose_trap",
        },
        "trap_verbose_file_handler": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/verbose_traps.log",
            "formatter": "verbose_trap",
        },
        "trap_common_file_handler": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/common_traps.log",
            "formatter": "verbose_trap",
        },
    },
    "loggers": {
        "": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": True,
        },
        "server_ntfc": {
            "level": "INFO",
            "handlers": ['server'],
            "propagate": True,
        },
        "penetrate_stage_log": {
            "level": "DEBUG",
            "handlers": ['file2'],
            "propagate": True,
        },
        "full_log": {
            "level": "INFO",
            "handlers": ['file'],
            "propagate": True,
        },
        "file_and_mail": {
            "level": "INFO",
            "handlers": ['file3'],
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
            "format": "{name} {levelname} {asctime} {message}",
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


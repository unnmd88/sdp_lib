import logging
import pprint
import tomllib
from collections.abc import (
    MutableMapping,
    Sequence
)
from enum import StrEnum
from functools import cached_property
from typing import NamedTuple

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib import logging_config


logger = logging.getLogger('server_ntfc')


class Fields(StrEnum):
    handlers = 'handlers'
    cycles = 'cycles'
    network_interfaces = 'network_interfaces'
    stdout_incoming_notifications = 'stdout_incoming_notifications'
    all_incoming_notifications = 'all_incoming_notifications'
    community = 'community'


class NetworkInterface(NamedTuple):
    ip: str
    port: int


class CycleConfig(NamedTuple):
    ip: str
    type_controller: AllowedControllers
    start_stage: int
    prom_tacts: MutableMapping = dict()


class ConfigParser:

    def __init__(self, source):
        self._source = source
        self._config = None
        self.parse_and_create()

    def parse_and_create(self):
        logger.info(f'{"*" * 25} Запуск trap сервера {"*" * 25}')
        logger.info(f'Читаю файл конфигурации {self._source}')
        self._read_file()
        logger.info(f'Файл конфигурации прочитан успешно')
        logger.info(f'Проверяю сетевые интерфейсы для приёма traps...')
        self._set_net_interfaces()
        logger.info(f'Проверка корректности сетевых интерфейсов выполнена успешно')
        if self.has_cycles:
            self._create_cycles_handler_data()
        logger.info(f'Файл конфигурации {self._source} прочитан успешно')
        pprint.pprint(self._config)

    def _read_file(self):
        try:
            with open(self._source, 'rb') as f:
                self._config = tomllib.load(f)
                pprint.pprint(self._config)
        except tomllib.TOMLDecodeError as e:
            logger.critical(f'Ошибка в файле {self._source}: {str(e)}')
            raise
        except FileNotFoundError as e:
            logger.critical(f'{str(e)}')
            raise

    def _set_net_interfaces(self):
        try:
            self._config[Fields.network_interfaces] = [
                NetworkInterface(*net_interface) for net_interface in self._config[Fields.network_interfaces]
            ]
        except KeyError as e:
            logger.critical(f'Нет зарегистрированных сетевых интерфейсов для приёма traps: {str(e)}')

    def _create_cycles_handler_data(self):
        try:
            cycles = self._config[Fields.handlers][Fields.cycles]
            self._config[Fields.handlers][Fields.cycles] = [CycleConfig(*cycle) for cycle in cycles]
        except KeyError:
            pass

    def get_handlers(self):
        return self._config.get(Fields.handlers)

    @property
    def net_interfaces(self) -> Sequence[NetworkInterface]:
        return self._config[Fields.network_interfaces]

    @property
    def community(self):
        return self._config[Fields.community]

    @property
    def has_handlers(self):
        return bool(self._config.get(Fields.handlers))

    @property
    def has_cycles(self) -> bool:
        try:
            return any(cyc for cyc in self._config[Fields.handlers][Fields.cycles])
        except KeyError:
            return False

    @property
    def cycles(self) -> list[CycleConfig]:
        try:
            return self._config[Fields.handlers][Fields.cycles]
        except KeyError:
            return []

    @cached_property
    def all_incoming_notifications(self) -> bool:
        try:
            return self._config[Fields.handlers][Fields.stdout_incoming_notifications]
        except (KeyError, AttributeError):
            return False

    @cached_property
    def stdout_incoming_notifications(self) -> bool:
        try:
            return self._config[Fields.handlers][Fields.stdout_incoming_notifications]
        except (KeyError, AttributeError):
            return False


if __name__ == '__main__':
    config = ConfigParser('config.toml')

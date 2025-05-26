import logging
import pprint
import tomllib
from collections.abc import (
    MutableMapping,
    Sequence
)
from enum import StrEnum
from functools import cached_property
from typing import NamedTuple, Any

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib import logging_config


logger = logging.getLogger('server_ntfc')


class Fields(StrEnum):
    """
    Класс содержит имена полей.
    """
    handlers = 'handlers'
    cycles = 'cycles'
    network_interfaces = 'network_interfaces'
    stdout_incoming_notifications = 'stdout_incoming_notifications'
    all_incoming_notifications = 'all_incoming_notifications'
    community = 'community'


class NetworkInterface(NamedTuple):
    """
    Является сущностью сетевого интерфейса для с ip и портом.
    """
    ip: str
    port: int


class CycleConfig(NamedTuple):
    """
    Конфигурация сущности для регистрации обработчика фаз и цикла.
    """
    ip: str
    type_controller: AllowedControllers
    start_stage: int
    prom_tacts: MutableMapping = dict()


class ConfigParser:
    """
    Парсер конфигурационного файла для настройки запуска сервера.
    """
    def __init__(self, source):
        self._source = source
        self._config = None
        self.parse_and_create()

    def parse_and_create(self):
        """
        Производит парсинг конфигурационного .toml файла
        и сохраняет данные в self._config для дальнейшего конфигурирования
        сервера и обработчиков входящих трап-сообщений.
        """
        logger.info(f'{"*" * 25} Запуск trap сервера {"*" * 25}')
        logger.info(f'Читаю файл конфигурации {self._source}')
        self._read_file()
        logger.info(f'Файл конфигурации прочитан успешно')
        logger.info(f'Проверяю сетевые интерфейсы для приёма traps...')
        self._create_net_interfaces_data()
        logger.info(f'Проверка корректности сетевых интерфейсов выполнена успешно')
        if self.has_cycles:
            self._create_cycles_handler_data()
        logger.info(f'Файл конфигурации {self._source} прочитан успешно')
        pprint.pprint(self._config)

    def _read_file(self):
        """
        Читает .toml файл и на его основе сохраняет данные в
        self._config.
        """
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

    def _create_net_interfaces_data(self):
        """
        Формирует данные о сетевых интерфейсах как экземпляры класса NetworkInterface
        и сохраняет их в self._config.
        """
        try:
            self._config[Fields.network_interfaces] = [
                NetworkInterface(*net_interface) for net_interface in self._config[Fields.network_interfaces]
            ]
        except KeyError as e:
            logger.critical(f'Нет зарегистрированных сетевых интерфейсов для приёма traps: {str(e)}')

    def _create_cycles_handler_data(self):
        """
        Формирует данные об обработчиках фаз и циклов как экземпляры класса CycleConfig
        и сохраняет их в self._config.
        """
        try:
            cycles = self._config[Fields.handlers][Fields.cycles]
            self._config[Fields.handlers][Fields.cycles] = [CycleConfig(*cycle) for cycle in cycles]
        except KeyError:
            pass

    def get_handlers(self) -> dict[str, Any]:
        """
        Возвращает словарь с данными обработчиков, указанных в файле .toml
        """
        return self._config.get(Fields.handlers)

    @property
    def net_interfaces(self) -> Sequence[NetworkInterface]:
        """
        Возвращает последовательность с сетевыми интерфесами.
        """
        return self._config[Fields.network_interfaces]

    @property
    def community(self) -> Sequence[tuple[str, str]]:
        """
        Возвращает последовательность с community.
        """
        return self._config[Fields.community]

    @property
    def has_handlers(self):
        """
        Возвращает True, если в конфиге есть 'handlers', иначе False.
        """
        return bool(self._config.get(Fields.handlers))

    @property
    def has_cycles(self) -> bool:
        """
        Возвращает True, если в конфиге есть обарботчики циклов и фаз, иначе False.
        """
        try:
            return any(cyc for cyc in self._config[Fields.handlers][Fields.cycles])
        except KeyError:
            return False

    @property
    def cycles(self) -> list[CycleConfig]:
        """
        Возвращает список с экземплярами CycleConfig. Если в конфигурационном
        файле данный сервис отсутствует, возвращает пустой список.
        """
        try:
            return self._config[Fields.handlers][Fields.cycles]
        except KeyError:
            return []

    @cached_property
    def all_incoming_notifications(self) -> bool:
        """
        Возвращает значение параметра all_incoming_notifications из .toml файла.
        """
        try:
            return self._config[Fields.handlers][Fields.stdout_incoming_notifications]
        except (KeyError, AttributeError):
            return False

    @cached_property
    def stdout_incoming_notifications(self) -> bool:
        """
        Возвращает значение параметра stdout_incoming_notifications из .toml файла.
        """
        try:
            return self._config[Fields.handlers][Fields.stdout_incoming_notifications]
        except (KeyError, AttributeError):
            return False


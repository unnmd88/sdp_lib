import ipaddress
from collections import deque
from collections.abc import (
    MutableMapping,
    MutableSequence,
    Iterable,
    Callable, Awaitable
)
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, NamedTuple

import aiohttp
from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.utils_common.utils_common import check_is_ipv4


class ResponseEntity(NamedTuple):
    raw_data: Any
    name: str = ''
    parser: Callable = None


@dataclass
class RequestResponse:
    name: str
    add_to_response_storage: bool
    parser: Callable = None
    coro: Awaitable | None = None
    method: Callable | None = None
    raw_response: str | None = None
    status_response: int | None = None
    errors: MutableSequence[str] = field(default_factory=list)
    processed_response: MutableMapping[str, Any] = field(default_factory=dict)

    def load_coro(self, coro: Awaitable):
        self.reset_data()
        self.coro = coro

    def load_raw_response(self, response: str):
        self.raw_response = response

    def load_error(self, error: str):
        self.errors.append(str(error))

    def load_status_response(self, status_response: int):
        self.status_response = status_response

    def reset_data(self):
        self.coro = None
        self.method = None
        self.raw_response = None
        self.status_response = None
        self.errors = []
        self.processed_response = {}


class Host:
    """
    Базовый класс хоста.
    """
    protocol: str

    def __init__(
            self,
            *,
            ipv4: str = None,
            host_id: str | int = None,
            driver = None
    ):
        self._ipv4 = ipv4
        self._driver = driver
        self.host_id = host_id
        self._tmp_response = None
        self._response_storage = ResponseStorage(self.protocol)
        self._storage = deque(maxlen=16)
        # self._varbinds_for_request = None

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'ipv4={self._ipv4} host_id={self.host_id} driver={self._driver}'
            f')'
        )

    def __getattr__(self, item):
        if 'stage' in item:
            return self._response_storage.processed_data_response.get(FieldsNames.curr_stage)
        raise AttributeError()

    def __setattr__(self, key, value):
        if key == '_ipv4':
            print(ipaddress.IPv4Address(value))
        super().__setattr__(key, value)

    @property
    def ip_v4(self):
        return self._ipv4

    def set_ipv4(self, ipv4: str):
        if ipv4 is None or check_is_ipv4(ipv4):
            self._ipv4 = ipv4
        else:
            raise ValueError(f'Значение < self.ipv4 > должно быть валидным ipv4 адресом: {ipv4}')

    @property
    def driver(self):
        return self._driver

    def set_driver(self, driver):
        if driver is None:
            return
        if  self.protocol == FieldsNames.protocol_snmp and  not isinstance(driver, SnmpEngine):
            raise TypeError(f'driver должен быть типа "SnmpEngine", передан: {type(driver)}')
        elif self.protocol == FieldsNames.protocol_http and not isinstance(driver, aiohttp.ClientSession):
            raise TypeError(f'driver должен быть типа "aiohttp.ClientSession", передан: {type(driver)}')
        # elif self.protocol == FieldsNames.protocol_ssh and not isinstance(driver, SSHClientConnection):
        #     raise TypeError(f'driver должен быть типа "SSHClientConnection", передан: {type(driver)}')
        self._driver = driver

    @property
    def response(self):
        return self._response_storage

    @property
    def response_as_dict(self):
        return self._response_storage.build_response_as_dict_from_raw_data_responses(self._ipv4)

    # def add_data_to_data_response_attrs(
    #         self,
    #         error: Exception | str = None,
    #         data: dict[str, Any] = None
    # ):
    #     self._response.add_data_to_attrs(error, data)

    def remove_data_from_response(self):
        self._response_storage.reset_processed_data_response()

    def remove_errors_from_response(self):
        self._response_storage.reset_errors()


class ResponseStorage:

    def __init__(self, protocol: str):
        self._protocol = protocol
        self._errors = []
        self._processed_data_response = {}
        self._storage_raw_responses: deque[ResponseEntity | RequestResponse] = deque(maxlen=8)
        self._storage = deque(maxlen=16)
    # def __repr__(self):
    #     processed_data_as_json = json.dumps(
    #         self.build_response_as_dict_from_raw_data_responses(ip_v4="Any ip_v4"), indent=4, ensure_ascii=False
    #         )
    #     return (
    #         f'{self.__class__.__name__}('
    #         f'errors={self._errors} raw_responses={self._storage_raw_responses}\n'
    #         f'processed_data_response:\n{processed_data_as_json}'
    #         f')'
    #     )

    @property
    def errors(self) -> MutableSequence[str]:
        return self._errors

    @cached_property
    def storage_raw_responses(self) -> MutableSequence[ResponseEntity]:
        return self._storage_raw_responses

    @property
    def processed_data_response(self) -> MutableMapping[str, Any]:
        return self._processed_data_response

    def put_raw_responses(self, *args: ResponseEntity | RequestResponse):
        for response in args:
            self._storage_raw_responses.append(response)

    def put_errors(self, *errors):
        for err in errors:
            self._errors.append(str(err))

    def build_response_as_dict_from_raw_data_responses(self, ip_v4: str):
        """
        Формирует словарь их self.response.
        После запроса, self.response принимает кортеж из 2 элементов:
        i[0] -> Строка с сообщением об ошибке, если в процессе запроса было возбуждено исключение, иначе None
        i[1] -> Словарь с распарсенными данными из ответа.
        :return: Словарь вида:
                 Если self.response[0] -> None(Нет ошибки):
                     "response": {
                          "protocol": "snmp",
                          "ip_address": "10.179.122.113",
                          "error": None,
                          "fixed_time_status": "0",
                          "plan_source": "7",
                          "current_status": "3_light",
                          "current_stage": 1,
                          "current_plan": "2",
                          "num_detectors": "5",
                          "status_soft_flag180_181": "00",
                          "current_mode": "VA"
                     }
                 Если self.response[0] -> "No SNMP response received before timeout"(Есть ошибка):
                     "response": {
                          "protocol": "snmp",
                          "ip_address": "10.45.154.16",
                          "error": "No SNMP response received before timeout"
                     }

        """
        self._processed_data_response = {}
        while self._storage_raw_responses:
            resp_data: ResponseEntity = self._storage_raw_responses.popleft()
            self._processed_data_response |= resp_data.parser(resp_data.raw_data)

        # Проверка, если FieldsNames.curr_mode None, то удаляем из словаря
        try:
            current_mode = self._processed_data_response.pop(FieldsNames.curr_mode)
            if current_mode is not None:
                self._processed_data_response[FieldsNames.curr_mode] = current_mode
        except KeyError:
            pass
        return {
            str(FieldsNames.protocol): self._protocol,
            str(FieldsNames.ipv4_address): ip_v4,
            str(FieldsNames.errors): ', '.join(str(e) for e in self._errors),
            str(FieldsNames.data): self._processed_data_response
        }

    def add_data_to_processed_response(self, data: MutableMapping[str, Any] | Iterable[tuple[str, Any]]):
        try:
            self._processed_data_response |= data
        except TypeError:
            for k, v in data:
                self._processed_data_response[k] = v

    def reset_all_data(self):
        self.reset_processed_data_response()
        self.reset_errors()

    def reset_processed_data_response(self):
        self._processed_data_response = {}

    def reset_errors(self):
        self._errors = deque(maxlen=8)


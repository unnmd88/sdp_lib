import asyncio
import ipaddress
import itertools
import json
from collections import deque
from collections.abc import (
    MutableMapping,
    MutableSequence,
    Iterable,
    Callable, Awaitable, Coroutine
)
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, NamedTuple, Self, Type

import aiohttp
from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.parser_core import Parsers
from sdp_lib.type_aliases import T_Parsers
from sdp_lib.utils_common.utils_common import check_is_ipv4


class ResponseEntity(NamedTuple):
    raw_data: Any
    name: str = ''
    parser: Callable = None


@dataclass(repr=False)
class RequestResponse:
    protocol: str
    add_to_response_storage: bool
    name: str = ''
    parser_obj: Any = None
    parser: Callable | T_Parsers = None
    coro: Awaitable | None = None
    data_to_handling: str | None = None
    status_response: int | None = None
    errors: MutableSequence[str] = field(default_factory=list)
    _processed_data: MutableMapping[str, Any] = field(default_factory=dict)

    def set_parser_obj(self, parser_obj: Callable):
        if not callable(parser_obj):
            raise ValueError(f'"parser_obj" должен быть вызываемым объектом')
        self.parser_obj = parser_obj

    def set_parse_method(self, method: Callable):
        if not callable(method):
            raise ValueError(f'"method" должен быть вызываемым объектом')
        self.parser = method

    def load_coro(self, coro: Awaitable):
        self.reset_data()
        self.coro = coro

    def load_raw_response(self, response: str):
        self.data_to_handling = response

    def load_error(self, error: str):
        self.errors.append(str(error))

    def load_status_response(self, status_response: int):
        self.status_response = status_response

    def reset_data(self):
        self.coro = None
        self.data_to_handling = None
        self.status_response = None
        self.errors = []
        self._processed_data = {}

    @cached_property
    def processed_pretty_data(self) -> MutableMapping[str, Any]:
        if not self._processed_data:
            self._processed_data = self.parser(self.data_to_handling)
        return self._processed_data


class Host:
    """
    Базовый класс хоста.
    """
    protocol: str
    _parser_class: Type[T_Parsers]

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
        self._request_storage = deque(maxlen=16)
        self._data_storage = ResponseStorage()
        self._processed_data_to_response = {}
        self._all_errors = []
        self._pattern_response = {
            str(FieldsNames.protocol): self.protocol,
            str(FieldsNames.ipv4_address): self._ipv4,
            str(FieldsNames.errors): self._all_errors,
            str(FieldsNames.data): self._processed_data_to_response
        }

        self._request_response_data_get_states = RequestResponse(
            protocol=self.protocol,
            name='get_state',
            add_to_response_storage=True,
            parser_obj=self._parser_class()
            # parser=self._parser_class()
        )
        self._request_response_data_default = RequestResponse(
            protocol=self.protocol,
            parser_obj=self._parser_class(),
            add_to_response_storage=True
        )

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'ipv4={self._ipv4} host_id={self.host_id} driver={self._driver}'
            f')'
        )

    def __getattr__(self, item):
        if 'stage' in item:
            return self._processed_data_to_response.get(FieldsNames.curr_stage)
        raise AttributeError()

    def __setattr__(self, key, value):
        if key == '_ipv4' and value:
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
    def data_storage(self):
        return self._data_storage.request_response_storage

    def clear_response_data(self):
        self._processed_data_to_response.clear()
        self._all_errors.clear()

    def build_response_as_dict(self):
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
        self.clear_response_data()

        # self._all_errors = [err for err in (obj.errors for obj in self.data_storage)]
        for err in (obj.errors for obj in self.data_storage):
            if err:
                self._all_errors.append(*err)

        print(f'self._all_errors: {self._all_errors}')
        if self._all_errors:
            self._processed_data_to_response.clear()
            self._data_storage.clear()
        else:
            while self.data_storage:
                resp_data: RequestResponse =self.data_storage.popleft()
                print(f'resp_data: {resp_data.data_to_handling}')
                print(f'resp_data: {resp_data.errors}')

                self._processed_data_to_response |= resp_data.processed_pretty_data

        # Проверка, если FieldsNames.curr_mode None, то удаляем из словаря
        try:
            current_mode = self._processed_data_to_response.pop(FieldsNames.curr_mode)
            if current_mode is not None:
                self._processed_data_to_response[FieldsNames.curr_mode] = current_mode
        except KeyError:
            pass
        print(f'self._processed_data_to_response: {self._processed_data_to_response}')
        return self._pattern_response

    async def _common_request(self) -> Self:
        pending = []
        print(self._request_storage)
        while self._request_storage:
            pending.append(asyncio.create_task(self._request_sender.common_request(self._request_storage.popleft())))
        # pending = [asyncio.create_task(req_resp.coro) for req_resp in self._storage]
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for done_task in done:
                await done_task
                request_response = done_task.result()
                if request_response.add_to_response_storage:
                    self._data_storage.put(request_response)
        return self

class ResponseStorage:

    def __init__(self):
        self._processed_data_to_response = {}
        self._storage_request_responses: deque[ResponseEntity | RequestResponse] = deque(maxlen=8)

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'storage_request_responses:\n{self._storage_request_responses} '
            f'processed_data_to_response={self._processed_data_to_response}'
            f')'
        )

    @cached_property
    def request_response_storage(self):
        return self._storage_request_responses

    def put(self, *args: ResponseEntity | RequestResponse):
        for response in args:
            self._storage_request_responses.append(response)

    def clear(self):
        self._storage_request_responses.clear()
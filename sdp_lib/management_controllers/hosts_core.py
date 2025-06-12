import json
from collections import deque
from collections.abc import MutableMapping, MutableSequence, Iterable, Callable
from functools import cached_property
from typing import Any, NamedTuple

import aiohttp
from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.structures import HostResponseStructure
from sdp_lib.utils_common.utils_common import check_is_ipv4


class ResponseEntity(NamedTuple):
    raw_data: Any
    name: str = ''
    parse_method: Callable = None


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
        # self._varbinds_for_request = None

    def __repr__(self):
        return (f'Host ipv4: {self._ipv4}\nHost id: {self.host_id}\n'
                f'Errors: {self._response_storage.errors}\n'
                f'Data: {self._response_storage.processed_data_response}\n'
                f'Response data as json:\n'
                f'{json.dumps(self.response_as_dict, indent=4, ensure_ascii=False)}')

    def __getattr__(self, item):
        if 'stage' in item:
            return self._response_storage.processed_data_response.get(FieldsNames.curr_stage)
        raise AttributeError()

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
        self._errors = deque(maxlen=8)
        self._processed_data_response = {}
        self._raw_response = None
        self._raw_responses: MutableSequence[ResponseEntity] = deque(maxlen=8)


    @property
    def errors(self) -> MutableSequence[str]:
        return self._errors

    @property
    def processed_data_response(self) -> MutableMapping[str, Any]:
        return self._processed_data_response

    @cached_property
    def raw_responses(self) -> MutableSequence[ResponseEntity]:
        return self._raw_responses

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
        for data in self._raw_responses:
            self._processed_data_response |= data.parse_method(data.raw_data)
        return {
            str(FieldsNames.protocol): self._protocol,
            str(FieldsNames.ipv4_address): ip_v4,
            str(FieldsNames.errors): self._errors,
            str(FieldsNames.data): self._processed_data_response
        }

    def add_data_to_processed_response_data(self, data: MutableMapping[str, Any] | Iterable[tuple[str, Any]]):
        try:
            self._processed_data_response |= data
        except TypeError:
            for k, v in data:
                self._processed_data_response[k] = v

    def add_errors(self, *errors):
        for err in errors:
            self._errors.append(str(err))

    # def add_data_to_attrs(
    #         self,
    #         error: Exception | str = None,
    #         data: dict[str, Any] = None
    # ):
    #     if isinstance(data, MutableMapping):
    #         self._processed_data_response |= data
    #     if isinstance(error, (Exception, str)):
    #         self._errors.append(error)

    def load_raw_response(self, raw_response):
        self.reset()
        self._raw_response = raw_response

    def reset(self):
        self.reset_processed_data_response()
        self.reset_errors()

    def reset_processed_data_response(self):
        self._processed_data_response = {}

    def reset_errors(self):
        self._errors = []


# class Response:
#
#     def __init__(self, protocol: str):
#         self._protocol = protocol
#         self._errors = deque(maxlen=8)
#         self._processed_data_response = {}
#         self._raw_response = None
#         self._response: list = [self._errors, self._processed_data_response, self._raw_response]
#
#     @property
#     def protocol(self) -> str:
#         return self._protocol
#
#     @property
#     def full(self) -> list[Any]:
#         return self._response
#
#     @property
#     def errors(self) -> MutableSequence[str]:
#         return self._errors
#
#     def load_raw_response(self):
#         self.clear()
#
#     @property
#     def data(self) -> MutableMapping[str, Any]:
#         return self._processed_data_response
#
#     def build_as_dict(self, ip_v4: str):
#         """
#         Формирует словарь их self.response.
#         После запроса, self.response принимает кортеж из 2 элементов:
#         i[0] -> Строка с сообщением об ошибке, если в процессе запроса было возбуждено исключение, иначе None
#         i[1] -> Словарь с распарсенными данными из ответа.
#         :return: Словарь вида:
#                  Если self.response[0] -> None(Нет ошибки):
#                      "response": {
#                           "protocol": "snmp",
#                           "ip_address": "10.179.122.113",
#                           "error": None,
#                           "fixed_time_status": "0",
#                           "plan_source": "7",
#                           "current_status": "3_light",
#                           "current_stage": 1,
#                           "current_plan": "2",
#                           "num_detectors": "5",
#                           "status_soft_flag180_181": "00",
#                           "current_mode": "VA"
#                      }
#                  Если self.response[0] -> "No SNMP response received before timeout"(Есть ошибка):
#                      "response": {
#                           "protocol": "snmp",
#                           "ip_address": "10.45.154.16",
#                           "error": "No SNMP response received before timeout"
#                      }
#
#         """
#         return {
#             str(FieldsNames.protocol): self._protocol,
#             str(FieldsNames.ipv4_address): ip_v4,
#             str(FieldsNames.errors): [str(e) for e in self._errors],
#             str(FieldsNames.data): self._processed_data_response
#         }
#
#     def add_data_to_attrs(
#             self,
#             error: Exception | str = None,
#             data: dict[str, Any] = None
#     ):
#         if isinstance(data, MutableMapping):
#             self._processed_data_response |= data
#         if isinstance(error, (Exception, str)):
#             self._errors.append(error)
#
#     def clear(self):
#         self.clear_processed_data_response()
#         self.clear_errors()
#
#     def clear_processed_data_response(self):
#         self._processed_data_response = {}
#
#     def clear_errors(self):
#         self._errors = []


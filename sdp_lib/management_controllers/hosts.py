import json
from typing import Any

import aiohttp
from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.response import Responses
from sdp_lib.utils_common.utils_common import check_is_ipv4


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
        self.last_response = None
        self._response = Responses(self.protocol)
        self._varbinds_for_request = None
        # self.ERRORS = []
        # self.DATA_RESPONSE = {}
        # self.RAW_RESPONSE = tuple()
        # self.response: list = [self.ERRORS, self.DATA_RESPONSE, self.RAW_RESPONSE]

    def __repr__(self):
        return (f'Host ipv4: {self._ipv4}\nHost id: {self.host_id}\n'
                f'Errors: {self._response.errors}\n'
                f'Data: {self._response.data}\n'
                f'Response data as json:\n'
                f'{json.dumps(self.response_as_dict, indent=4, ensure_ascii=False)}')

    # def __setattr__(self, key, value):
    #     if key == 'ip_v4':
    #         if value is None or check_is_ipv4(value):
    #             self.__dict__[key] = value
    #         else:
    #             raise ValueError(f'Значение < self.ipv4 > должно быть валидным ipv4 адресом: {value}')
    #
    #     elif key == 'scn':
    #         if value is None or len(value) <= 10:
    #             self.__dict__[key] = value
    #         else:
    #             raise ValueError('Значение < self.scn > не должно превышать 10 символов ')
    #     else:
    #         self.__dict__[key] = value

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
        return self._response

    @property
    def response_errors(self) -> list:
        return self._response.errors

    @property
    def response_data(self) -> dict:
        return self._response.data

    @property
    def response_as_dict(self):
        return self._response.build_as_dict(self._ipv4)

    def add_data_to_data_response_attrs(
            self,
            error: Exception | str = None,
            data: dict[str, Any] = None
    ):
        self._response.add_data_to_attrs(error, data)

    def remove_data_from_response(self):
        self._response.remove_data_from_data_response()

    def remove_errors_from_response(self):
        self._response.remove_errors_from_errors()



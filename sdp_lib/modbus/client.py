from collections import deque
from collections.abc import (
    Iterable,
    MutableMapping,
    Sequence
)
import ipaddress
from functools import cached_property

from pyModbusTCP.client import ModbusClient

from sdp_lib.modbus.formatters import Formatter

class ResponseEntity:
    def __init__(self):
        self._data = None
        self._errors = deque(maxlen=8)

    @property
    def errors(self):
        return self._errors

    @property
    def data(self):
        return self._data

    def add_errors(self, *args: str | Exception):
        for err in args:
            self._errors.append(str(err))

    def set_data(self, data):
        self._data = data

    def reset_all(self):
        self._errors.clear()
        self._data = None


class Modbus:
    def __init__(
            self,
            *,
            ipv4: str,
            port: int = 502,
            bit_address_to_description: Iterable[tuple[int, str]] | MutableMapping[int, str] = None
    ):
        self._ipv4 = str(ipaddress.IPv4Address(ipv4))
        self._port = port
        self._mb_client = ModbusClient(host=self._ipv4, port=port, timeout=2)
        self._response = ResponseEntity()
        self._recv_formatter = Formatter(bit_address_to_description)
        self._start_bit_addr = 0
        self._num_bits_to_read = 8

    @cached_property
    def client(self):
        return self._mb_client

    @cached_property
    def recv_formatter(self):
        return self._recv_formatter

    @cached_property
    def ipv4(self):
        return self._ipv4

    @cached_property
    def port(self):
        return self._port

    @property
    def response_data(self):
        return self._response.data

    @property
    def response_errors(self):
        return self._response.errors

    def read_discrete_inputs(self) -> list[bool] | None:
        return self._mb_client.read_discrete_inputs(self._start_bit_addr, self._num_bits_to_read)

    def read_discrete_inputs_and_process(self):
        self._response.reset_all()
        dig_inputs = self.read_discrete_inputs()
        if dig_inputs is None:
            self._response.add_errors(f'Ошибка соединения...')
        else:
            recv_as_string = self._recv_formatter.states_as_pretty_string(dig_inputs)
            self._response.set_data(recv_as_string)






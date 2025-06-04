from collections.abc import (
    Iterable,
    MutableMapping,
    Sequence
)
import ipaddress
from functools import cached_property

from pyModbusTCP.client import ModbusClient

from sdp_lib.modbus.formatters import Formatter


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

    def read_discrete_inputs(self) -> list[bool] | None:
        return self._mb_client.read_discrete_inputs(self._start_bit_addr, self._num_bits_to_read)

    def read_discrete_inputs_and_process_as_string(self) -> str:
        dig_inputs = self.read_discrete_inputs()
        if dig_inputs is None:
            return f'Ошибка соединения...'
        return self._recv_formatter.states_as_pretty_string(dig_inputs)





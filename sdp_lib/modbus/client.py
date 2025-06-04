from collections.abc import (
    Iterable,
    MutableMapping,
    Sequence
)
import ipaddress

from pyModbusTCP.client import ModbusClient


class ModbusStages:
    def __init__(self, ipv4: str, port: int = 502):
        self._ipv4 = str(ipaddress.IPv4Address(ipv4))
        self._port = port
        self._mb_client = ModbusClient(host=self._ipv4, port=port, timeout=2)
        self._start_bit_addr = 0
        self._num_bits_to_read = 8
        self._curr_states_DI = None
        self._matched_stages_and_bits = {}

    @property
    def modbus_client(self):
        return self._mb_client

    @property
    def ipv4(self):
        return self._ipv4

    @property
    def port(self):
        return self._port

    def bind_bits_to_stages(self, bits_to_stages: Iterable[Sequence[int, int]] | MutableMapping[int, int]):
        if isinstance(bits_to_stages, MutableMapping):
            bits_to_stages = bits_to_stages.items()
        for bit_addr, stage in bits_to_stages:
            self._matched_stages_and_bits[bit_addr] = stage

    def read_digital_inputs(self) -> list[bool]:
        return self._mb_client.read_discrete_inputs(self._start_bit_addr, self._num_bits_to_read)

    def read_dig_inputs_and_process(self):
        dig_inputs = self.read_digital_inputs()
        if dig_inputs is None:
            return f'Ошибка соединения...'
        return self.process_dig_inputs(dig_inputs)

    def process_dig_inputs(self, dig_inputs: list[bool]) -> str:
        data = ''
        for i, dig_inp in enumerate(dig_inputs):
            try:
                stage = f' (Stage={self._matched_stages_and_bits[i]})'
            except KeyError:
                stage = ''
            data += f' <DI={i} State={int(dig_inp)}{stage}>'
        return data


class Formatter:
    def __init__(self, matched_val_to_state = None):
        self._matched_val_to_state = {}
        self.bind_bits_addr_to_value(matched_val_to_state)

    def bind_bits_addr_to_value(self, state_to_val: Iterable[Sequence[int, int]] | MutableMapping[int, int]):

        if not state_to_val:
            return

        if isinstance(state_to_val, MutableMapping):
            state_to_val = state_to_val.items()
        for bit_addr, val in state_to_val:
            self._matched_val_to_state[bit_addr] = val

    def get_bindings_bits_addr_to_val(self):
        return self._matched_val_to_state

    def states_as_pretty(self, states: list[bool]):
        pass



if __name__ == '__main__':
    ob = Formatter({0: 1, 1: 2, 4: 6})
    print(ob.get_bindings_bits_addr_to_val())


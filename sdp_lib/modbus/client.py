import asyncio
import typing
from collections import deque, ChainMap
from collections.abc import (
    Iterable,
    MutableMapping,
    Sequence
)
import ipaddress
from functools import cached_property
from typing import Any, NamedTuple, TypeAlias, TypeVar, AnyStr

from pyModbusTCP.client import ModbusClient

from sdp_lib.modbus.data_helpers import Description
from sdp_lib.modbus.fields import FieldNames
from sdp_lib.modbus.formatters import Formatter
from sdp_lib.type_aliases import alias_matched_bit_states_to_descr, alias_matched_bit_addr_to_descr


class ResponseEntity:
    def __init__(self):
        self._set_default_data()
        self._errors = deque(maxlen=8)

    def _set_default_data(self):
        self._data = {FieldNames.pretty: None, FieldNames.current_stage: None}

    @property
    def errors(self) -> Sequence[str]:
        return self._errors

    @property
    def data(self) -> MutableMapping:
        return self._data

    def add_errors(self, *args: str | Exception):
        for err in args:
            self._errors.append(str(err))

    def put_data(self, data: MutableMapping | Iterable[Iterable[Any, Any]]):
        try:
            self._data |= data
        except TypeError:
            for k, v in data:
                self._data[k] = v

    def put_data_to_pretty_field_name(self, data: Any):
        self.put_data([(FieldNames.pretty, data)])

    def put_stage_to_current_data_field_name(self, val: int):
        self.put_data([(FieldNames.current_stage, val)])

    def clear_errors(self):
        self._errors.clear()

    def clear_data(self):
        self._data.clear()

    def reset_errors_and_data(self):
        self._errors.clear()
        self._set_default_data()

    def clear_errors_and_data(self):
        self._errors.clear()
        self._data.clear()


class Modbus:

    protocol = 'modbus'

    def __init__(
            self,
            *,
            ipv4: str,
            port: int = 502,
            matched_bit_states_to_description: alias_matched_bit_states_to_descr,
            matched_bit_addr_to_description: alias_matched_bit_addr_to_descr = None,
            bad_value_expected_val: Any = -1
    ):
        self._ipv4 = str(ipaddress.IPv4Address(ipv4))
        self._port = port
        self._mb_client = ModbusClient(host=self._ipv4, port=port, timeout=.6, auto_close=True)
        self._response = ResponseEntity()
        self._matched_bit_states_to_description = dict(matched_bit_states_to_description)
        self._matched_bit_addr_to_description = dict(matched_bit_addr_to_description or {})
        self._bad_value_expected_val = bad_value_expected_val
        self._start_bit_addr = 0
        self._num_bits_to_read = 8

    def __getattr__(self, item):
        if FieldNames.current_stage in item:
            return self._response.data.get(FieldNames.current_stage)
        raise AttributeError()

    @cached_property
    def client(self):
        return self._mb_client

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

    @cached_property
    def matched_bit_states_to_description(self):
        return self._matched_bit_states_to_description

    @cached_property
    def matched_bit_address_to_description(self):
        return self._matched_bit_addr_to_description

    def read_discrete_inputs(self) -> list[bool] | None:
        return self._mb_client.read_discrete_inputs(self._start_bit_addr, self._num_bits_to_read)

    def read_discrete_inputs_and_process(self):
        self._response.reset_errors_and_data()
        dig_inputs = self.read_discrete_inputs()
        self.process_response_discrete_inputs(dig_inputs)

    def process_response_discrete_inputs(self, dig_inputs: list[bool]):
        if dig_inputs is None:
            self._response.add_errors(f'Ошибка соединения...')
        else:
            self._response.reset_errors_and_data()
            recv = self.create_data(dig_inputs)
            self._response.put_data_to_pretty_field_name(recv.string_pattern)
            self._response.put_stage_to_current_data_field_name(recv.expected_val)

    def get_expected_val_from_states(self, states: list[bool]):
        try:
            description = self._matched_bit_states_to_description[tuple(states)]
            return description.expected_val
        except KeyError:
            return self._bad_value_expected_val

    def create_data(self, states: list[bool]) -> Description:
        string_data = ''
        for i, state in enumerate(states):
            try:
                d = self._matched_bit_addr_to_description[i]
                description = d.string_pattern
            except KeyError:
                description = ''
            state_as_str = f'State={int(state)}'
            string_data += f' <Bit address={i} {state_as_str}{description}>'
        return Description(string_data, self.get_expected_val_from_states(states))


class AsyncModbus(Modbus):

    async def read_discrete_inputs(self) -> list[bool] | None:
        return await asyncio.to_thread(
            self._mb_client.read_discrete_inputs, self._start_bit_addr, self._num_bits_to_read
        )

    async def read_discrete_inputs_and_process(self):
        self._response.reset_errors_and_data()
        dig_inputs = await self.read_discrete_inputs()
        self.process_response_discrete_inputs(dig_inputs)

    async def get_current_stage(self):
        await self.read_discrete_inputs_and_process()
        return self


def create_bits_pattern(bits_pattern: Iterable[bool | int | AnyStr]):
    return tuple(bool(int(val)) for val in bits_pattern)


if __name__ == '__main__':
    stage1 = Description('(Stage=1)', 1)
    stage4 = Description('(Stage=4)', 4)
    stage5 = Description('(Stage=5)', 5)
    stage7 = Description('(Stage=7)', 7)
    bit_states_to_description = {
        create_bits_pattern([0, 0, 0, 0, 1, 0, 1, 0]):                               stage1,
        create_bits_pattern([False, False, True, False, True, False, False, False]): stage4,
        create_bits_pattern([0, 0, 0, 1, 1, 0, 1, 0]):                               stage5,
        create_bits_pattern('00011000'):                                             stage7,
        FieldNames.ignored_bits: {4}
    }
    bit_address_to_description = {6: stage1, 2: stage4, 3: stage5, 5:stage7}

    # modbus_client = Modbus(ipv4=ip, port=port, bit_address_to_description=bit_to_description)

    modbus_client = AsyncModbus(
        ipv4='91.227.113.186',
        port=502,
        matched_bit_states_to_description=bit_states_to_description,
        # matched_bit_addr_to_description=bit_address_to_description
    )
    print(modbus_client.matched_bit_states_to_description)
    print(modbus_client.matched_bit_address_to_description)
    print(create_bits_pattern('00011000'))
    print(modbus_client.create_data([False, False, True, False, True, False, False, False]))
    modbus_client.process_response_discrete_inputs([False, False, True, False, True, False, False, False])
    print(modbus_client.response_data)
    print(modbus_client.response_errors)
    # polling(modbus_client, 1)

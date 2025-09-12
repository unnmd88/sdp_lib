import os
from collections import deque
from collections.abc import (
    MutableMapping,
    MutableSequence
)
from abc import abstractmethod
from typing import (
    NamedTuple,
    TypeAlias
)

from dotenv import load_dotenv

from sdp_lib.management_controllers.http.peek.static_data import Actuator


load_dotenv()

all_mpp_inputs = set(os.getenv('ALL_MPP_INPUTS').split())
mpp_stages_inputs = {INP_NAME: int(INP_NAME[-1]) for INP_NAME in os.getenv('MPP_STAGES_INPUTS').split()}
MPP_MAN = os.getenv('MPP_MANUAL')
PREFIX_MAN_STAGE_PEEK = os.getenv('PREFIX_MAN_STAGE_PEEK')
MPP_PH = os.getenv('PREFIX_MAN_STAGE_PEEK')
START_NAME_MAN = os.getenv('START_NAME_MAN')

key_payload = 'par_name'
val_payload = 'par_value'
inputs_prefix = os.getenv('INPUT_PREFIX_FOR_SET_VAL')


class Payload(NamedTuple):
    name: str
    data: tuple[tuple[str, str], tuple[str, str]]


def create_payload(
    index: str,
    prefix: str,
    actuator: str,
    name: str
) -> Payload:
    if actuator in (Actuator.VF_as_chars, Actuator.ON_as_chars, Actuator.OFF_as_chars):
        actuator = Actuator.get_reverse_value(actuator)
    name = Actuator.pretty_print(name, actuator)
    return Payload(name=name, data=((key_payload, f'{prefix}{index}'), (val_payload, actuator)))


T_inp_props = tuple[str, str, str, str, str]
T_inps_container = list[tuple[str, str]] | tuple[tuple[str, str], ...] | dict[str, str]
T_storage_to_send: TypeAlias = MutableSequence[MutableSequence[Payload]] | deque[MutableSequence[Payload]]


class AbstractPayloads:
    _prefix: str
    _index: int
    _num:int
    _name:int
    _state:int
    _state_time:int
    _actuator:int

    def __init__(self, processed_data: MutableMapping | None = None):
        self._processed_data = processed_data
        self._storage_to_send: T_storage_to_send = deque()
        if self._processed_data is not None:
            pass # инициализировать доп атрибуты
    
    @property
    def storage_to_send(self):
        return self._storage_to_send
    
    def _add_payloads_to_send(self, *payloads):
        for payload in payloads:
            self._storage_to_send.append(payload)
    
    def clear_storage_to_send(self):
        self._storage_to_send.clear()
    
    def load_processed_data(self, data):
        self._processed_data = data

    @abstractmethod
    def create_payloads(self, value: str | int):
        """ Создает коллекцию с payloads для отправки команды хосту. """
        ...


class InputsPayloads(AbstractPayloads):

    _prefix = inputs_prefix

    def _add_payloads_to_container_if_actuator_not_on(self, *inp_names):
        for inp_name in inp_names:
            index, num, name, state, state_time, actuator = self._processed_data[inp_name]
            if state == '0' or actuator != Actuator.ON_as_chars:
                yield create_payload(index, self._prefix, Actuator.ON_as_value, name)

    def _create_payload_reset_man_and_add_to_container(self, *inp_names):
        for inp_name in inp_names:
            index, num, name, state, state_time, actuator = self._processed_data[inp_name]
            actuator_val = None
            match (state, actuator):
                case('1', Actuator.VF_as_chars) if inp_name == MPP_MAN:
                    actuator_val = Actuator.OFF_as_value
                case ('1', Actuator.ON_as_chars):
                    actuator_val = Actuator.VF_as_value
                case('0', Actuator.OFF_as_chars):
                    actuator_val = Actuator.VF_as_value
            if actuator_val:
                yield create_payload(index, self._prefix, actuator_val, name)

    def create_reset_man_payloads(self):
        self.clear_storage_to_send()
        first_group_to_send, second_group_to_send = [], []
        self._add_payloads_to_send(first_group_to_send, second_group_to_send)
        first_group_to_send += self._create_payload_reset_man_and_add_to_container(MPP_MAN)
        second_group_to_send += self._create_payload_reset_man_and_add_to_container(*mpp_stages_inputs)
        return self._storage_to_send

    def create_payloads(self, stage: int):
        
        stage_as_str = str(int(stage))
        if stage_as_str == '0':
            return self.create_reset_man_payloads()
        self.clear_storage_to_send()
        first_group_to_send, second_group_to_send = [], []
        self._add_payloads_to_send(first_group_to_send, second_group_to_send)
        first_group_to_send += self._add_payloads_to_container_if_actuator_not_on(f'{MPP_PH}{stage_as_str}')
        second_group_to_send += self._add_payloads_to_container_if_actuator_not_on(MPP_MAN)
        stack = {k for k in mpp_stages_inputs if k != f'{MPP_PH}{stage_as_str}'}
        while stack:
            index, num, name, state, state_time, actuator = self._processed_data[stack.pop()]
            if state != '0' or actuator == Actuator.ON_as_chars:
                first_group_to_send.append(create_payload(index, self._prefix, Actuator.OFF_as_value, name))
        return self._storage_to_send


if __name__ == '__main__':
    print({int(_MPP_PH[-1]): _MPP_PH for _MPP_PH in mpp_stages_inputs})
    print(set(mpp_stages_inputs))
    inps = {'MKEY1': ('0', '1', 'MKEY1', '0', '2345563', '-'), 'MKEY2': ('1', '2', 'MKEY2', '0', '2345563', '-'), 'MKEY3': ('2', '3', 'MKEY3', '0', '2345563', '-'), 'MKEY4': ('3', '4', 'MKEY4', '0', '2345563', '-'), 'MKEY5': ('4', '5', 'MKEY5', '0', '2345563', '-'), 'KEY10': ('5', '6', 'KEY10', '0', '2345563', '-'), 'KEY11': ('6', '7', 'KEY11', '0', '2345563', '-'), 'KEY12': ('7', '8', 'KEY12', '0', '2345563', '-'), 'MPP_MAN': ('8', '9', 'MPP_MAN', '0', '2345563', '-'), 'MPP_FL': ('9', '10', 'MPP_FL', '0', '2345563', '-'), 'MPP_OFF': ('10', '11', 'MPP_OFF', '0', '2345563', '-'), 'MPP_PH1': ('11', '12', 'MPP_PH1', '0', '2345563', '-'), 'MPP_PH2': ('12', '13', 'MPP_PH2', '0', '2345563', '-'), 'MPP_PH3': ('13', '14', 'MPP_PH3', '0', '2345563', '-'), 'MPP_PH4': ('14', '15', 'MPP_PH4', '0', '2345563', '-'), 'MPP_PH5': ('15', '16', 'MPP_PH5', '0', '2345563', '-'), 'MPP_PH6': ('16', '17', 'MPP_PH6', '0', '2345563', '-'), 'MPP_PH7': ('17', '18', 'MPP_PH7', '0', '2345563', '-'), 'MPP_PH8': ('18', '19', 'MPP_PH8', '0', '2345563', '-'), 'MPP_QPH': ('19', '20', 'MPP_QPH', '0', '2345563', '-'), 'MPP_GL1': ('20', '21', 'MPP_GL1', '0', '2345563', '-'), 'MPP_GL2': ('21', '22', 'MPP_GL2', '0', '2345563', '-'), 'MPP_GL3': ('22', '23', 'MPP_GL3', '0', '2345563', '-'), 'MPP_GL4': ('23', '24', 'MPP_GL4', '0', '2345563', '-'), 'MPP_AUT': ('24', '25', 'MPP_AUT', '1', '2345558', '-'), 'CP_OFF': ('25', '26', 'CP_OFF', '0', '2345563', '-'), 'CP_FLASH': ('26', '27', 'CP_FLASH', '0', '2345563', '-'), 'CP_RED': ('27', '28', 'CP_RED', '0', '2345563', '-'), 'CP_AUTO': ('28', '29', 'CP_AUTO', '0', '2345563', '-'), 'CP_FIX': ('29', '30', 'CP_FIX', '0', '2345563', '-'), 'MIMIC': ('30', '31', 'MIMIC', '0', '2345563', '-')}
    obj = InputsPayloads(inps)
    print(obj.create_payloads(0))

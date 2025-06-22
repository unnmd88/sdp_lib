import itertools
import os
from collections import deque
from collections.abc import MutableMapping, Sequence
from abc import abstractmethod

from dotenv import load_dotenv

from sdp_lib.management_controllers.http.peek.static_data import (
    ActuatorAsChar,
    ActuatorAsValue, matches_actuators
)
from sdp_lib.management_controllers.structures import InputsStructure


load_dotenv()

all_mpp_inputs = set(os.getenv('ALL_MPP_INPUTS').split())
# mpp_stages_inputs = set(os.getenv('MPP_STAGES_INPUTS').split())
mpp_stages_inputs = {INP_NAME: int(INP_NAME[-1]) for INP_NAME in os.getenv('MPP_STAGES_INPUTS').split()}
MPP_MAN = os.getenv('MPP_MANUAL')
PREFIX_MAN_STAGE_PEEK = os.getenv('PREFIX_MAN_STAGE_PEEK')
MPP_PH = os.getenv('PREFIX_MAN_STAGE_PEEK')
START_NAME_MAN = os.getenv('START_NAME_MAN')

key_payload = 'par_name'
val_payload = 'par_value'
inputs_prefix = os.getenv('INPUT_PREFIX_FOR_SET_VAL')


def get_actuator_val_for_payload(value):
    if value in [el for el in ActuatorAsValue]:
        return value
    elif value in [el for el in ActuatorAsChar]:
        return matches_actuators.get(value)
    else:
        raise ValueError(f'Некорректное значение актуатора: {value!r}')


T_inp_props = tuple[str, str, str, str, str]
T_inps_container = list[tuple[str, str]] | tuple[tuple[str, str], ...] | dict[str, str]


class InputsVarbinds:

    def __init__(self, inputs_from_web: dict[str, T_inp_props] = None):
        self._inputs_from_web = None
        self._mpp_man_index = None
        self._mpp_man_state = None
        self._mpp_man_actuator = None
        self.set_inputs_from_web_data(inputs_from_web)

    def set_inputs_from_web_data(self, inputs_from_web) -> None:
        self._inputs_from_web = inputs_from_web
        if self._inputs_from_web is not None:
            self._mpp_man_index = self._inputs_from_web[MPP_MAN][InputsStructure.INDEX]
            self._mpp_man_state = self._inputs_from_web[MPP_MAN][InputsStructure.STATE]
            self._mpp_man_actuator = self._inputs_from_web[MPP_MAN][InputsStructure.ACTUATOR]

    def refresh_inputs_from_web_data(self, inputs_from_web):
        self.set_inputs_from_web_data(inputs_from_web)

    def get_varbinds_as_from_name(self, data: T_inps_container) -> list:

        payloads = []

        if isinstance(data, dict):
            data = data.items()

        for inp_name, actuator_val in data:
            if (inp_name in self._inputs_from_web
                and self._inputs_from_web[inp_name][InputsStructure.ACTUATOR] != actuator_val
            ):
                payloads.append(
                    self.create_payload(self._inputs_from_web[inp_name][InputsStructure.INDEX], actuator_val)
                )
        return payloads

    def get_varbinds_set_stage(self, stage: int = 0) -> list:

        if stage == 0:
            return self.get_varbinds_reset_man()
        elif stage in range(1, 9):
            return self._get_varbinds_set_stage(stage)

    def _get_varbinds_set_stage(self, stage: int) -> list:
        payloads = []
        if self._mpp_man_state == '0' or self._mpp_man_actuator in (ActuatorAsChar.VF, ActuatorAsChar.OFF):
            payloads.append(
                self.create_payload(self._mpp_man_index, ActuatorAsValue.ON)
            )

        # stage = str(stage)
        mpp_ph_to_set = f'{PREFIX_MAN_STAGE_PEEK}{stage}'
        for mpp in mpp_stages_inputs:

            if (mpp != mpp_ph_to_set
                and self._inputs_from_web[mpp][InputsStructure.STATE] != '0'
                and self._inputs_from_web[mpp][InputsStructure.ACTUATOR] != ActuatorAsChar.OFF
            ):
                payloads.append(
                    self.create_payload(self._inputs_from_web[mpp][InputsStructure.INDEX], ActuatorAsValue.OFF)
                )
        if self._inputs_from_web[mpp_ph_to_set][InputsStructure.ACTUATOR] != ActuatorAsChar.ON:
            payloads.append(
                self.create_payload(self._inputs_from_web[mpp_ph_to_set][InputsStructure.INDEX], ActuatorAsValue.ON)
            )
        return payloads

    def get_varbinds_reset_man(self) -> list:
        payloads = []
        if (self._inputs_from_web[MPP_MAN][InputsStructure.STATE] == '1'
            or self._inputs_from_web[MPP_MAN][InputsStructure.ACTUATOR] == ActuatorAsChar.ON
        ):
            payloads.append(
                self.create_payload(self._inputs_from_web[MPP_MAN][InputsStructure.INDEX], ActuatorAsValue.OFF)
            )

        for mpp_inp in mpp_stages_inputs:
            # if (self._inputs_from_web[mpp_inp][InputsStructure.STATE] == '1'
            #    or self._inputs_from_web[mpp_inp][InputsStructure.ACTUATOR] != ActuatorAsChar.VF
            # ):
            if self._inputs_from_web[mpp_inp][InputsStructure.ACTUATOR] != ActuatorAsChar.VF:
                payloads.append(
                    self.create_payload(self._inputs_from_web[mpp_inp][InputsStructure.INDEX], ActuatorAsValue.VF)
                )
        return payloads

    def create_payload(self, inp_index: str, actuator_val: ActuatorAsValue | str) -> tuple:

        return (
            (key_payload, f'{inputs_prefix}{inp_index}'),
            (val_payload, get_actuator_val_for_payload(actuator_val))
        )


class AbtrsctEntity:
    _prefix: str
    _index: int
    _num:int
    _name:int
    _state:int
    _state_time:int
    _actuator:int

    def __init__(self, processed_data: MutableMapping | None = None):
        self._processed_data = processed_data
        self._storage_to_send = deque()
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

    def get_payload(self, index: str, actuator_val: ActuatorAsChar | str) -> tuple:
        return (
            (key_payload, f'{self._prefix}{index}'),
            (val_payload, get_actuator_val_for_payload(actuator_val))
        )

    @abstractmethod
    def create_payloads(self, value: str | int):
        """ Создает коллекцию с payloads для отправки команды хосту. """
        ...


class Inputs(AbtrsctEntity):
    _prefix = inputs_prefix

    # def set_inputs_from_web_data(self, inputs_from_web) -> None:
    #     self._inputs_from_web = inputs_from_web
    #     if self._inputs_from_web is not None:
    #         self._mpp_man_index = self._inputs_from_web[MPP_MAN][InputsStructure.INDEX]
    #         self._mpp_man_state = self._inputs_from_web[MPP_MAN][InputsStructure.STATE]
    #         self._mpp_man_actuator = self._inputs_from_web[MPP_MAN][InputsStructure.ACTUATOR]
    #
    # def refresh_inputs_from_web_data(self, inputs_from_web):
    #     self.set_inputs_from_web_data(inputs_from_web)
    #
    # def get_varbinds_as_from_name(self, data: T_inps_container) -> list:
    #
    #     payloads = []
    #
    #     if isinstance(data, dict):
    #         data = data.items()
    #
    #     for inp_name, actuator_val in data:
    #         if (inp_name in self._inputs_from_web
    #             and self._inputs_from_web[inp_name][InputsStructure.ACTUATOR] != actuator_val
    #         ):
    #             payloads.append(
    #                 self.create_payload(self._inputs_from_web[inp_name][InputsStructure.INDEX], actuator_val)
    #             )
    #     return payloads
    #
    # def get_varbinds_set_stage(self, stage: int = 0) -> list:
    #
    #     if stage == 0:
    #         return self.get_varbinds_reset_man()
    #     elif stage in range(1, 9):
    #         return self._get_varbinds_set_stage(stage)
    #
    # def _get_varbinds_set_stage(self, stage: int) -> list:
    #     payloads = []
    #     if self._mpp_man_state == '0' or self._mpp_man_actuator in (ActuatorAsChar.VF, ActuatorAsChar.OFF):
    #         payloads.append(
    #             self.create_payload(self._mpp_man_index, ActuatorAsValue.ON)
    #         )
    #
    #     # stage = str(stage)
    #     mpp_ph_to_set = f'{PREFIX_MAN_STAGE_PEEK}{stage}'
    #     for mpp in mpp_stages_inputs:
    #
    #         if (mpp != mpp_ph_to_set
    #             and self._inputs_from_web[mpp][InputsStructure.STATE] != '0'
    #             and self._inputs_from_web[mpp][InputsStructure.ACTUATOR] != ActuatorAsChar.OFF
    #         ):
    #             payloads.append(
    #                 self.create_payload(self._inputs_from_web[mpp][InputsStructure.INDEX], ActuatorAsValue.OFF)
    #             )
    #     if self._inputs_from_web[mpp_ph_to_set][InputsStructure.ACTUATOR] != ActuatorAsChar.ON:
    #         payloads.append(
    #             self.create_payload(self._inputs_from_web[mpp_ph_to_set][InputsStructure.INDEX], ActuatorAsValue.ON)
    #         )
    #     return payloads
    #
    # def get_varbinds_reset_man(self) -> list:
    #     payloads = []
    #     if (self._inputs_from_web[MPP_MAN][InputsStructure.STATE] == '1'
    #         or self._inputs_from_web[MPP_MAN][InputsStructure.ACTUATOR] == ActuatorAsChar.ON
    #     ):
    #         payloads.append(
    #             self.create_payload(self._inputs_from_web[MPP_MAN][InputsStructure.INDEX], ActuatorAsValue.OFF)
    #         )
    #
    #     for mpp_inp in mpp_stages_inputs:
    #         # if (self._inputs_from_web[mpp_inp][InputsStructure.STATE] == '1'
    #         #    or self._inputs_from_web[mpp_inp][InputsStructure.ACTUATOR] != ActuatorAsChar.VF
    #         # ):
    #         if self._inputs_from_web[mpp_inp][InputsStructure.ACTUATOR] != ActuatorAsChar.VF:
    #             payloads.append(
    #                 self.create_payload(self._inputs_from_web[mpp_inp][InputsStructure.INDEX], ActuatorAsValue.VF)
    #             )
    #     return payloads
    
    def _add_to_send_if_actuator_not_on(self, *inp_names):
        for inp_name in inp_names:
            index, num, name, state, state_time, actuator = self._processed_data[inp_name]
            if state == '0' or actuator != ActuatorAsChar.ON:
                self._add_payloads_to_send(create_payload(index, self._prefix, ActuatorAsValue.ON))

    def create_reset_man_payloads(self):
        for inp_name in itertools.chain(mpp_stages_inputs, (MPP_MAN, )):
            index, num, name, state, state_time, actuator = self._processed_data[inp_name]
            if state != '0' or actuator != ActuatorAsChar.VF:
                self._storage_to_send.append(create_payload(index, self._prefix, ActuatorAsValue.VF))
        return self._storage_to_send

    def create_payloads(self, stage: int):
        
        self.clear_storage_to_send()
        stage_as_str = str(int(stage))
        if stage_as_str == '0':
            return self.create_reset_man_payloads()
        self._add_to_send_if_actuator_not_on(MPP_MAN, f'{MPP_PH}{stage_as_str}')
        stack = {k for k in mpp_stages_inputs if k != f'{MPP_PH}{stage_as_str}'}
        while stack:
            index, num, name, state, state_time, actuator = self._processed_data[stack.pop()]
            if state != '0' or actuator == ActuatorAsChar.ON:
                self._add_payloads_to_send(create_payload(index, self._prefix, ActuatorAsValue.OFF))
        return self._storage_to_send

def create_payload(
    index: str, 
    prefix: str, 
    val: str
) -> tuple:

    return (key_payload, f'{prefix}{index}'), (val_payload, val)
        
        
    

    # return (
    #     (key_payload, f'{inputs_prefix}{inp_index}'),
    #     (val_payload, get_actuator_val_for_payload(actuator_val))
    # )


def create_request_payloads_set_stage_man(
    inputs_from_web: MutableMapping[str, Sequence[str, str, str, str, str, str]],
    stage: int
):
    data = deque()
    stack = set(mpp_stages_inputs)

    index, num, name, state, state_time, actuator = inputs_from_web[MPP_MAN]
    if state == '0' or actuator != ActuatorAsChar.ON:
        data.append()

    stage_as_str = str(stage)
    stage_to_set = stack.remove(f'{PREFIX_MAN_STAGE_PEEK}{stage_as_str}')

    while stack:
        index, num, name, state, state_time, actuator = inputs_from_web[stack.popleft()]


if __name__ == '__main__':
    print({int(_MPP_PH[-1]): _MPP_PH for _MPP_PH in mpp_stages_inputs})
    print(set(mpp_stages_inputs))
    inps = {'MKEY1': ('0', '1', 'MKEY1', '0', '2345563', '-'), 'MKEY2': ('1', '2', 'MKEY2', '0', '2345563', '-'), 'MKEY3': ('2', '3', 'MKEY3', '0', '2345563', '-'), 'MKEY4': ('3', '4', 'MKEY4', '0', '2345563', '-'), 'MKEY5': ('4', '5', 'MKEY5', '0', '2345563', '-'), 'KEY10': ('5', '6', 'KEY10', '0', '2345563', '-'), 'KEY11': ('6', '7', 'KEY11', '0', '2345563', '-'), 'KEY12': ('7', '8', 'KEY12', '0', '2345563', '-'), 'MPP_MAN': ('8', '9', 'MPP_MAN', '0', '2345563', '-'), 'MPP_FL': ('9', '10', 'MPP_FL', '0', '2345563', '-'), 'MPP_OFF': ('10', '11', 'MPP_OFF', '0', '2345563', '-'), 'MPP_PH1': ('11', '12', 'MPP_PH1', '0', '2345563', '-'), 'MPP_PH2': ('12', '13', 'MPP_PH2', '0', '2345563', '-'), 'MPP_PH3': ('13', '14', 'MPP_PH3', '0', '2345563', '-'), 'MPP_PH4': ('14', '15', 'MPP_PH4', '0', '2345563', '-'), 'MPP_PH5': ('15', '16', 'MPP_PH5', '0', '2345563', '-'), 'MPP_PH6': ('16', '17', 'MPP_PH6', '0', '2345563', '-'), 'MPP_PH7': ('17', '18', 'MPP_PH7', '0', '2345563', '-'), 'MPP_PH8': ('18', '19', 'MPP_PH8', '0', '2345563', '-'), 'MPP_QPH': ('19', '20', 'MPP_QPH', '0', '2345563', '-'), 'MPP_GL1': ('20', '21', 'MPP_GL1', '0', '2345563', '-'), 'MPP_GL2': ('21', '22', 'MPP_GL2', '0', '2345563', '-'), 'MPP_GL3': ('22', '23', 'MPP_GL3', '0', '2345563', '-'), 'MPP_GL4': ('23', '24', 'MPP_GL4', '0', '2345563', '-'), 'MPP_AUT': ('24', '25', 'MPP_AUT', '1', '2345558', '-'), 'CP_OFF': ('25', '26', 'CP_OFF', '0', '2345563', '-'), 'CP_FLASH': ('26', '27', 'CP_FLASH', '0', '2345563', '-'), 'CP_RED': ('27', '28', 'CP_RED', '0', '2345563', '-'), 'CP_AUTO': ('28', '29', 'CP_AUTO', '0', '2345563', '-'), 'CP_FIX': ('29', '30', 'CP_FIX', '0', '2345563', '-'), 'MIMIC': ('30', '31', 'MIMIC', '0', '2345563', '-')}
    obj = Inputs(inps)
    print(obj.create_payloads(0))

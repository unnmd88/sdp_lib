import os

from sdp_lib.management_controllers.http.peek.static_data import (
    ActuatorAsChar,
    ActuatorAsValue, matches_actuators
)
from sdp_lib.management_controllers.structures import InputsStructure


all_mpp_inputs = set(os.getenv('ALL_MPP_INPUTS').split())
mpp_stages_inputs = set(os.getenv('MPP_STAGES_INPUTS').split())
MPP_MAN = os.getenv('MPP_MANUAL')
PREFIX_MAN_STAGE_PEEK = os.getenv('PREFIX_MAN_STAGE_PEEK')
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


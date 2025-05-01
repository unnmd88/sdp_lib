import abc
import asyncio
import os

import aiohttp

from sdp_lib.management_controllers.exceptions import BadValueToSet
from sdp_lib.management_controllers.http.peek import routes, web_inputs
from sdp_lib.management_controllers.http.peek.management.management_core import SetData, ActuatorAsValue, ActuatorAsChar
from sdp_lib.management_controllers.http.peek.monitoring.inputs import InputsPage


# web_page_class = InputsPage
# ROUTE = routes.set_inputs
# PREFIX_PAR_NAME = web_inputs.prefix_set_val
#
# ALL_MPP_INPUTS = set(os.getenv('ALL_MPP_INPUTS').split())
# MPP_STAGES_INPUTS = set(web_inputs.mpp_stages_inputs.split())
#
# NUM       = 1
# NAME      = 2
# STATE     = 3
# TIME      = 4
# ACTUATOR  = 5

class SetInputsDataClass(SetData, abc.ABC):

    web_page_class = InputsPage
    route = routes.set_inputs
    prefix_par_name = web_inputs.prefix_set_val

    all_mpp_inputs = set(os.getenv('ALL_MPP_INPUTS').split())
    mpp_stages_inputs = set(web_inputs.mpp_stages_inputs.split())

    NUM        = 1
    NAME       = 2
    STATE      = 3
    TIME       = 4
    ACTUATOR   = 5


class SetStage(SetInputsDataClass):

    def make_values_to_set(self, stage_value: int) -> dict[str, int]:
        """

        Пример name и props:
        name          -> 'MPP_PH2'
        props         -> ('9', '10', 'MPP_PH2', '1', '1', '-')
        {name: props} ->  {'MPP_PH2': ('9', '10', 'MPP_PH2', '1', '1', '-')}
        :param stage_value:
        :return:
        """
        if stage_value == 0:
            return self.make_values_to_reset_man()

        if not isinstance(stage_value,  int):
            raise TypeError('Значение должно быть целым числом')
        elif stage_value not in range(1, 9):
            raise BadValueToSet(value=stage_value, expected=(1, 9))

        data = {}
        for name, props in self.web_page_obj.parser.parsed_content_as_dict.items():
            if name in self.mpp_stages_inputs and int(name[-1]) != stage_value:
                data[name] = int(ActuatorAsValue.OFF)

        mpp_man: web_inputs.input_properties = self.web_page_obj.parser.parsed_content_as_dict[web_inputs.mpp_man]
        mpp_stage: web_inputs.input_properties = (
            self.web_page_obj.parser.parsed_content_as_dict[f'{web_inputs.prefix_mpp_stage}{str(stage_value)}']
        )
        if mpp_man[self.STATE] == '0' or mpp_man[self.ACTUATOR] != ActuatorAsChar.ON:
            data[web_inputs.mpp_man] = int(ActuatorAsValue.ON)
        if mpp_stage[self.STATE] == '0' or mpp_stage[self.ACTUATOR] != ActuatorAsChar.ON:
            data[f'{web_inputs.prefix_mpp_stage}{str(stage_value)}'] = int(ActuatorAsValue.ON)

        print(f'part2 data: {data}')
        return data

    def make_values_to_reset_man(self) -> dict[str, int]:
        data = {web_inputs.mpp_man: 1}
        return data | {name: 0 for name in self.mpp_stages_inputs}


class SetFlash(SetInputsDataClass):

    def make_values_to_set(self, stage_value: int) -> dict[str, int]:
        """

        Пример name и props:
        name          -> 'MPP_PH2'
        props         -> ('9', '10', 'MPP_PH2', '1', '1', '-')
        {name: props} ->  {'MPP_PH2': ('9', '10', 'MPP_PH2', '1', '1', '-')}
        :param stage_value:
        :return:
        """
        if stage_value == 0:
            return {web_inputs.mpp_flash: int(ActuatorAsValue.OFF)}
        elif stage_value == 1:
            return {web_inputs.mpp_flash: int(ActuatorAsValue.ON)}
        else:
            raise BadValueToSet(value=stage_value, expected=(0, 1))


async def main():
    async with aiohttp.ClientSession() as sess:
        obj = SetStage(ipv4='10.179.112.241', session=sess)
        obj = SetStage(ipv4='10.179.107.129', session=sess)
        # obj = SetInputs(ip_v4='10.45.154.19')
        # obj = SetInputs(ip_v4='10.179.20.9')

        return await obj.set_entity(0)


if __name__ == '__main__':

    r = asyncio.run(main())
    print(r.response_as_model)
    print(*r.response_as_model[0])



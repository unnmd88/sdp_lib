import abc
import asyncio
from enum import StrEnum
from typing import Type

import aiohttp

from sdp_lib.management_controllers.exceptions import ErrorSetValue, BadValueToSet
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.http.peek.monitoring.multiple import T
from sdp_lib.management_controllers.http.peek.peek_core import PeekWeb


class ActuatorAsChar(StrEnum):
    VF     = '-'
    OFF    = 'ВЫКЛ'
    ON     = 'ВКЛ'


class ActuatorAsValue(StrEnum):
    VF     = '0'
    OFF    = '1'
    ON     = '2'


class SetData(PeekWeb):

    web_page_class: Type[T]

    prefix_par_name: str

    INDEX = 0

    def __init__(self, ipv4: str, session: aiohttp.ClientSession):
        super().__init__(ipv4=ipv4, session=session)
        self.web_page_obj: T = self.web_page_class(self._ipv4, self._driver)
        self.method = self.post
        self.data_for_set_to_web = None

    async def set_any_vals(
            self,
            data_to_set: dict[str, str | int],
            start_by_getting_data_from_web_page=False
    ):
        print(f'start_by_getting_data_from_web_page: {start_by_getting_data_from_web_page}')
        if start_by_getting_data_from_web_page:
            result = await self.get_data_from_web_page_and_set_response_if_has_err()
            if not result:
                return self

        sending_result = await self.create_tasks_and_send_request_to_set_val(
            data_from_web=self.web_page_obj.parser.parsed_content_as_dict,
            data_for_set=data_to_set,
            prefix=self.prefix_par_name,
            index=self.INDEX
        )

        if not self.check_sending_result_and_set_response_if_has_err(sending_result):
            return self

        await self.web_page_obj.get_and_parse()
        # self.response = self.web_page_obj.response
        print(f'self.web_page_obj.response>: {self.web_page_obj._data}')
        self.add_data_to_data_response_attrs(*self.web_page_obj._data)
        self.add_data_to_data_response_attrs(data={str(FieldsNames.sent_data): self.data_for_set_to_web})
        print(f'self.data_for_set_to_web: {self.data_for_set_to_web}')

        print(f'self.response: {self.response}')
        return self

    async def get_data_from_web_page_and_set_response_if_has_err(self) -> bool:
        await self.web_page_obj.get_and_parse()
        print(f'self.web_page_obj.response_errors: {self.web_page_obj.response_errors}')
        if self.web_page_obj.response_errors:
            self.add_data_to_data_response_attrs(*self.web_page_obj.processed_data_response)
            return False
        return True

    async def create_tasks_and_send_request_to_set_val(
            self,
            *,
            data_from_web: dict[str, str],
            data_for_set: dict[str, int],
            prefix: str,
            index: int
    ):
        async with asyncio.TaskGroup() as tg:
            res = [
                tg.create_task(
                    self.http_request_to_host(
                        payload=self.get_payload(inp, val, data_from_web, prefix, index)
                    )
                )
                    for inp, val in data_for_set.items()
            ]
        return res

    def get_payload(
            self,
            inp_name: str,
            val: float,
            data: dict,
            prefix: str,
            index: int | None
    ):
        param_index = '' if index is None else data.get(inp_name)[index]
        return {'par_name': f'{prefix}{param_index}', 'par_value': val}

    def check_sending_result_and_set_response_if_has_err(self,sending_result) -> bool:
        print(f'!!: {[res_task.result() for res_task in sending_result]}')
        if any(res_task.result()[self.RESPONSE] != 200 for res_task in sending_result):
            self.add_data_to_data_response_attrs(ErrorSetValue())
            return False
        return True

    async def set_entity(self, value: int):

        result = await self.get_data_from_web_page_and_set_response_if_has_err()
        if not result:
            return self

        try:
            self.data_for_set_to_web = self.make_values_to_set(value)
        except BadValueToSet as e:
            self.add_data_to_data_response_attrs(e)
            return self

        print(self.data_for_set_to_web)
        print(len(self.data_for_set_to_web))
        return await self.set_any_vals(self.data_for_set_to_web)

    @abc.abstractmethod
    def make_values_to_set(self, value: int) -> dict[str, int]:
        ...
import asyncio
from asyncio import TaskGroup
from functools import cached_property
from typing import Callable

import aiohttp

from sdp_lib.management_controllers.constants import Names
from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.hosts_core import Host
from sdp_lib.management_controllers.http.peek import routes
from sdp_lib.management_controllers.http.request_sender import AsyncHttpRequests
from sdp_lib.management_controllers.parsers.parsers_peek_http_new import MainPageParser, InputsPageParser
from sdp_lib.management_controllers.response_structure import HttpResponseStructure
from sdp_lib.utils_common import check_is_ipv4


class HttpHosts(Host):

    protocol = FieldsNames.protocol_http

    def __init__(self, ipv4: str = None, host_id = None, session: aiohttp.ClientSession = None):
        super().__init__(ipv4=ipv4, host_id=host_id)
        self._base_url = f'{Names.http_prefix}{self._ipv4}' if ipv4 is not None else ''
        self.set_driver(session)
        self._request_sender = AsyncHttpRequests(self)
        self._request_method: Callable | None = None
        # self._parse_method_config = None
        self._parser = None
        self._varbinds_for_request = None

    def set_base_url(self):
        if check_is_ipv4(self._ipv4):
            self._base_url = f'{Names.http_prefix}{self._ipv4}'
        else:
            self._base_url = ''

    @property
    def base_url(self):
        return self._base_url

    def check_http_response_errors_and_add_to_host_data_if_has(self):
        """

        """
        if self.last_response[HttpResponseStructure.ERROR] is not None:
            self.add_data_to_data_response_attrs(self.last_response[HttpResponseStructure.ERROR])
        return bool(self.response_errors)


class PeekWeb(HttpHosts):

    @cached_property
    def matches(self) -> dict:
        return {
            'main_page_get': (routes.main_page, self._request_sender.fetch, MainPageParser),
            'inputs_page_get': (routes.get_inputs, self._request_sender.fetch, InputsPageParser)
        }

    async def _single_common_request(
            self,
            url,
            method: Callable,
            parser
    ):
        self.last_response = await self._request_sender.http_request_to_host(
            url=url,
            method=method
        )
        if self.check_http_response_errors_and_add_to_host_data_if_has():
            return self

        parser.parse(self.last_response[HttpResponseStructure.CONTENT])
        if not parser.data_for_response:
            self.add_data_to_data_response_attrs(error=BadControllerType())
        else:
            self.add_data_to_data_response_attrs(
                data=parser.data_for_response
            )
        return self

    async def request_all_types(self, *args, **kwargs):
        async with asyncio.TaskGroup() as tg:
            for page in args:
                route, method, parser_class = self.matches.get(page)
                tg.create_task(
                    self._single_common_request(
                        self._base_url + route, method, parser_class()
                    )
                )
        if self.response_errors:
            self.remove_data_from_response()
        return self

    async def get_states(self):
        return await self.request_all_types('main_page_get')


async def main():
    try:
        sess = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(1))
        obj = PeekWeb('10.179.107.129', host_id='2406', session=sess)
        # await obj.get_states()
        await obj.request_all_types('inputs_page_get')
    finally:
        await sess.close()

    print(obj)




if __name__ == '__main__':
    res = asyncio.run(main())
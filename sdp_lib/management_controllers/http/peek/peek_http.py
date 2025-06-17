import asyncio
import time
from collections.abc import Awaitable, MutableSequence, MutableMapping
from dataclasses import dataclass, field
from enum import IntEnum
from functools import cached_property
from typing import (
    Callable,
    Type,
    TypeVar, TypeAlias, Any, Self
)

import aiohttp

from sdp_lib.management_controllers.exceptions import (
    BadControllerType,
    BadValueToSet
)
from sdp_lib.management_controllers.hosts_core import ResponseEntity, RequestResponse
from sdp_lib.management_controllers.http.http_core import HttpHosts
from sdp_lib.management_controllers.http.peek import (
    routes,
    static_data
)
from sdp_lib.management_controllers.http.peek.varbinds import InputsVarbinds
from sdp_lib.management_controllers.parsers.parsers_peek_http_new import (
    MainPageParser,
    InputsPageParser, PeekWebPagesParser,
)
from sdp_lib.management_controllers.structures import HttpResponseStructure


T_Parsers = TypeVar('T_Parsers', MainPageParser, InputsPageParser)




class DataFromWeb(IntEnum):

    main_page_get     = 1
    inputs_page_get   = 2
    inputs_page_set   = 3


# class PeekWebHosts(HttpHosts):
#
#     @cached_property
#     def matches(self) -> dict[DataFromWeb, tuple[str, Callable, Type[T_Parsers]]]:
#         return {
#             DataFromWeb.main_page_get: (routes.main_page, self._request_sender.fetch, PeekWebPagesParser),
#             DataFromWeb.inputs_page_get: (routes.get_inputs, self._request_sender.fetch, InputsPageParser),
#             DataFromWeb.inputs_page_set: (routes.set_inputs, self._request_sender.post_request, None),
#         }
#
#     async def _single_common_request(
#             self,
#             url,
#             method: Callable,
#             parser_class,
#             **kwargs
#     ):
#         self._tmp_response = await self._request_sender.http_request_to_host(
#             url=url,
#             method=method,
#             **kwargs
#         )
#         if self.check_http_response_errors_and_add_to_host_data_if_has():
#             return self
#
#         # print(f'self.last_response: {self.last_response}')
#
#         # if parser_class is None:
#         #     # Вернуть ответ из self._request_sender.http_request_to_host если парсер не задан
#         #     return self._tmp_response[HttpResponseStructure.CONTENT]
#
#         parser = PeekWebPagesParser()
#         # parsed_data = parser.main_page_parser.parse()
#
#         # parser = parser_class()
#         # parser.parse(self._tmp_response[HttpResponseStructure.CONTENT])
#         # print(f'parser.data_for_response: {parser.data_for_response}')
#
#         self._response_storage.put_raw_responses(ResponseEntity(
#             raw_data=self._tmp_response[HttpResponseStructure.CONTENT],
#             name='PeekWeb',
#             parser=parser.main_page_parser.parse
#         ))
#
#         return self
#
#     """ Monitoring """
#
#     async def fetch_all_pages(self, *args, **kwargs):
#         async with asyncio.TaskGroup() as tg:
#             for page in args:
#                 route, method, parser_class = self.matches.get(page)
#                 tg.create_task(
#                     self._single_common_request(
#                         self._base_url + route, method, parser_class,
#                         **kwargs
#                     )
#                 )
#         # if self.response_errors:
#         #     self.remove_data_from_response()
#         return self
#
#     async def get_states(self):
#         return await self.fetch_all_pages(DataFromWeb.main_page_get)
#
#     async def get_inputs(self):
#         return await self.fetch_all_pages(DataFromWeb.inputs_page_get)
#
#     """ Management """
#
#     async def post_all_pages(self, page, payload_data: list[tuple]):
#         async with asyncio.TaskGroup() as tg:
#             results = []
#             print(f'page: {page}\npayload: {payload_data}')
#             route, method, parser_class = self.matches.get(page)
#             max_concurrent_tasks = 5
#             for num_task, payload in enumerate(payload_data, 1):
#                 if num_task % max_concurrent_tasks == 0:
#                     print(f'DEBUG len(payload_data) : {len(payload_data)}')
#                     await asyncio.sleep(1) # Peek сбрасывает при коннект при большом количестве запросов
#                 results.append(
#                     tg.create_task(
#                         self._single_common_request(
#                             self._base_url + route, method, parser_class,
#                             cookies=static_data.cookies,
#                             data=payload
#                         )
#                     )
#                 )
#
#         # print(f'results_results: + {results}')
#         if self.response_errors:
#             self.remove_data_from_response()
#         return self
#
#     async def set_inputs_to_web(
#             self,
#             *,
#             inps_name_and_vals: dict | tuple = None,
#             stage: int = None,
#     ):
#         await self.get_inputs()
#         if self.response_errors:
#             return self
#         _inputs = self.response_as_dict['data']['inputs']
#
#         if stage is not None:
#             payloads = InputsVarbinds(_inputs).get_varbinds_set_stage(stage)
#         else:
#             payloads = InputsVarbinds(_inputs).get_varbinds_as_from_name(inps_name_and_vals)
#
#         print(f'payloads: {payloads}')
#         await self.post_all_pages(
#             DataFromWeb.inputs_page_set,
#             payload_data=payloads
#         )
#         await self.get_inputs()
#         return self
#
#     async def set_stage(self, stage: int):
#
#         if stage not in range(9):
#             self.add_data_to_data_response_attrs(BadValueToSet(value=stage, expected=(0, 8)))
#             return self
#         return await self.set_inputs_to_web(stage=stage)


class PeekWebHosts(HttpHosts):

    _parser_class = PeekWebPagesParser

    def __init__(self, ipv4: str = None, host_id = None, session: aiohttp.ClientSession = None):
        super().__init__(ipv4=ipv4, host_id=host_id, session=session)
        self._parser = self._parser_class()
        self._request_response_get_states = RequestResponse(
            protocol=self.protocol,
            name='get_state',
            add_to_response_storage=True,
            parser=self._parser.main_page_parser.parse
        )

    @cached_property
    def matches(self) -> dict[DataFromWeb, tuple[str, Callable, Type[T_Parsers]]]:
        return {
            DataFromWeb.main_page_get: (routes.main_page, self._request_sender.fetch, PeekWebPagesParser),
            DataFromWeb.inputs_page_get: (routes.get_inputs, self._request_sender.fetch, InputsPageParser),
            DataFromWeb.inputs_page_set: (routes.set_inputs, self._request_sender.post_request, None),
        }

    async def _single_common_request(
            self,
            url,
            method: Callable,
            parser_class,
            **kwargs
    ):
        self._tmp_response = await self._request_sender.http_request_to_host(
            url=url,
            method=method,
            **kwargs
        )
        if self.check_http_response_errors_and_add_to_host_data_if_has():
            return self

        # print(f'self.last_response: {self.last_response}')

        # if parser_class is None:
        #     # Вернуть ответ из self._request_sender.http_request_to_host если парсер не задан
        #     return self._tmp_response[HttpResponseStructure.CONTENT]

        parser = PeekWebPagesParser()
        # parsed_data = parser.main_page_parser.parse()

        # parser = parser_class()
        # parser.parse(self._tmp_response[HttpResponseStructure.CONTENT])
        # print(f'parser.data_for_response: {parser.data_for_response}')

        self._data_storage.put(ResponseEntity(
            raw_data=self._tmp_response[HttpResponseStructure.CONTENT],
            name='PeekWeb',
            parser=parser.main_page_parser.parse,
        ))

        return self

    """ Monitoring """

    async def get_states(self):

        self._request_response_get_states.load_coro(self._request_sender.fetch(self._base_url + routes.main_page))
        self._request_storage.append(self._request_response_get_states)
        return await self._common_request()

    async def get_inputs(self):
        return await self.fetch_all_pages(DataFromWeb.inputs_page_get)

    """ Management """

    async def post_all_pages(self, page, payload_data: list[tuple]):
        async with asyncio.TaskGroup() as tg:
            results = []
            print(f'page: {page}\npayload: {payload_data}')
            route, method, parser_class = self.matches.get(page)
            max_concurrent_tasks = 5
            for num_task, payload in enumerate(payload_data, 1):
                if num_task % max_concurrent_tasks == 0:
                    print(f'DEBUG len(payload_data) : {len(payload_data)}')
                    await asyncio.sleep(1) # Peek сбрасывает при коннект при большом количестве запросов
                results.append(
                    tg.create_task(
                        self._single_common_request(
                            self._base_url + route, method, parser_class,
                            cookies=static_data.cookies,
                            data=payload
                        )
                    )
                )

        # print(f'results_results: + {results}')
        if self.response_errors:
            self.remove_data_from_response()
        return self

    async def set_inputs_to_web(
            self,
            *,
            inps_name_and_vals: dict | tuple = None,
            stage: int = None,
    ):
        await self.get_inputs()
        if self.response_errors:
            return self
        _inputs = self.response_as_dict['data']['inputs']

        if stage is not None:
            payloads = InputsVarbinds(_inputs).get_varbinds_set_stage(stage)
        else:
            payloads = InputsVarbinds(_inputs).get_varbinds_as_from_name(inps_name_and_vals)

        print(f'payloads: {payloads}')
        await self.post_all_pages(
            DataFromWeb.inputs_page_set,
            payload_data=payloads
        )
        await self.get_inputs()
        return self

    async def set_stage(self, stage: int):

        if stage not in range(9):
            self.add_data_to_data_response_attrs(BadValueToSet(value=stage, expected=(0, 8)))
            return self
        return await self.set_inputs_to_web(stage=stage)


""" Tests """

async def main():
    """
    Тестовая функция.
    """
    sess = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(1))
    try:
        obj = PeekWebHosts('10.179.75.113', host_id='3290', session=sess)
        start_time = time.perf_counter()

        await obj.get_states()
        print(obj.build_response_as_dict())
        print(f'время составило: {time.perf_counter() - start_time}')
        # await obj.request_all_types(AvailableDataFromWeb.main_page_get)
        # await obj.set_inputs_to_web(inps_name_and_vals=(('MPP_PH2', '-'),
        #                                                 ('MPP_MAN', '-'),
        #                                                 ('MPP_PH3', 'ВКЛ'),
        #                                                 ('MPP_PH4', '0')))

        # await obj.get_states()
    except RuntimeError:
        print(sess.closed)

    finally:
        await sess.close()

    # print(obj)




if __name__ == '__main__':
    res = asyncio.run(main())
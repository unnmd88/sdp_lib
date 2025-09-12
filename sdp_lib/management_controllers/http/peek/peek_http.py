import asyncio
import json
import time
from collections.abc import (
    MutableSequence,
    Sequence
)
from enum import IntEnum
from functools import cached_property
from typing import (
    Callable,
    Type,
    TypeVar
)

import aiohttp

from sdp_lib.management_controllers.exceptions import BadValueToSet
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.hosts_core import RequestResponse
from sdp_lib.management_controllers.http.http_core import HttpHosts
from sdp_lib.management_controllers.http.peek import (
    routes,
    static_data
)
from sdp_lib.management_controllers.http.peek.varbinds import (
    InputsPayloads,
    Payload
)
from sdp_lib.management_controllers.parsers.parsers_peek_http import (
    MainPageParser,
    InputsPageParser,
    PeekWebPagesParser,
    SetInputsPageParser,
)


T_Parsers = TypeVar('T_Parsers', MainPageParser, InputsPageParser)


class DataFromWeb(IntEnum):

    main_page_get     = 1
    inputs_page_get   = 2
    inputs_page_set   = 3


class PeekWebHosts(HttpHosts):

    _parser_class = PeekWebPagesParser
    _ok_alert = 'alert_msg = "";'

    def __init__(self, ipv4: str = None, host_id = None, session: aiohttp.ClientSession = None):
        super().__init__(ipv4=ipv4, host_id=host_id, session=session)
        self._semaphore = asyncio.Semaphore(value=6)
        self._request_response_data_get_states.set_parse_method(
            self._request_response_data_get_states.parser_obj.main_page_parser.sort
        )

    @cached_property
    def matches(self) -> dict[DataFromWeb, tuple[str, Callable, Type[T_Parsers]]]:
        return {
            DataFromWeb.main_page_get: (routes.main_page, self._request_sender.fetch, MainPageParser),
            DataFromWeb.inputs_page_get: (routes.get_inputs, self._request_sender.fetch, InputsPageParser),
            DataFromWeb.inputs_page_set: (routes.set_inputs, self._request_sender.post_request, None),
        }

    def build_request_response(self, data_from_web: DataFromWeb):
        route, method, parser_class = self.matches[data_from_web]
        parser = parser_class()

        return RequestResponse(
                    protocol=self.protocol,
                    add_to_response_storage=True,
                    parser_obj=parser,
                    parser=parser.sort,
                    coro=method(self._base_url + route, self._semaphore)
                )

    """ Monitoring """

    async def get_states(self, *extras: DataFromWeb):
        self._request_storage.clear()
        self._request_response_data_get_states.load_coro(
            self._request_sender.fetch(self._base_url + routes.main_page, self._semaphore)
        )
        self._request_storage.append(self._request_response_data_get_states)
        for data_from_web in extras:
            DataFromWeb(data_from_web)
            self._request_storage.append(self.build_request_response(data_from_web))
        return await self._common_request()

    async def generate_data_and_send_http_request(self, *pages: DataFromWeb, clear_storage: bool = True):
        if clear_storage:
            self._request_storage.clear()
        for page in pages:
            self._request_storage.append(self.build_request_response(page))
        return await self._common_request()

    async def get_inputs(self):
        return await self.generate_data_and_send_http_request(DataFromWeb.inputs_page_get, clear_storage=True)

    """ Management """

    async def _make_request_and_process_response(
            self,
            payloads: Sequence[Payload],
            retries: int = 1
    ) -> tuple[MutableSequence[str], MutableSequence[str]]:
        success, faults,  pending = [], [], []
        for retry in range(retries):
            for payload in payloads:
                pending.append(
                    asyncio.create_task(
                        self._request_sender.post_request(
                            url=self._base_url + routes.set_inputs,
                            semaphore=self._semaphore,
                            cookies=static_data.cookies,
                            data=payload.data
                        ),
                        name=payload.name
                    )
                )
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for done_task in done:
                    await done_task
                    error, status, content = done_task.result()
                    if error is None and status == 200 and self._ok_alert in content:
                        success.append(done_task.get_name())
                    else:
                        faults.append(done_task.get_name())
            if not faults:
                break
        return success, faults

    async def set_stage(self, stage: int):
        stage = int(stage)
        if not 0 <= stage <= 8:
            self._request_response_data_default.load_error(str(BadValueToSet(value=stage, expected=(0, 8))))
            self._data_storage.put(self._request_response_data_default)
            return self

        request_response_inputs = await self._request_sender.common_request(
            self.build_request_response(DataFromWeb.inputs_page_get)
        )
        if request_response_inputs.errors:
            return self

        inps_data = InputsPayloads(request_response_inputs.processed_pretty_data['inputs'])
        success_sent, faults_sent = [], []
        for payloads in inps_data.create_payloads(stage):
            ok, faults = await self._make_request_and_process_response(payloads)
            faults_sent += faults
            if faults:
                faults_sent += faults
                self._request_response_data_default.load_error(f'Ошибка установки ВВОДОВ: {faults_sent}')
                self._data_storage.put(self._request_response_data_default)
                return self
            success_sent += ok
        parser = SetInputsPageParser()
        request_response = RequestResponse(
            name=FieldsNames.set_stage,
            parser_obj=parser,
            parser=parser.parse,
            protocol=self.protocol,
            add_to_response_storage=True
        )
        if not faults_sent:
            data_to_response = {FieldsNames.set_stage: int(stage)}
        else:
            data_to_response = {FieldsNames.set_stage: f'Ошибка установки фазы {int(stage)}'}
        request_response.load_raw_response(data_to_response)
        self._data_storage.put(request_response)
        return self


""" Tests """

async def main():
    """
    Тестовая функция.
    """
    sess = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(1))
    try:
        # obj = PeekWebHosts('10.179.75.113', host_id='3290', session=sess)
        obj = PeekWebHosts('10.179.107.129', host_id='2406', session=sess)
        start_time = time.perf_counter()

        await obj.get_states()
        # await obj.generate_data_and_send_http_request(DataFromWeb.main_page_get, DataFromWeb.inputs_page_get)
        # await obj.get_inputs()
        # await obj.set_stage(0)
        print(json.dumps(obj.build_response_as_dict(), indent=4, ensure_ascii=False))
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
    msg_alert_example = ['<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Frameset//EN">\n<html>\n<head>\n<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n<link href="style.css" rel="stylesheet" type="text/css">\n<!--[if IE]>\n<link href="style_ie.css" rel="stylesheet" type="text/css">\n<![endif]-->\n<script type=\'text/javascript\' language=\'javascript\' SRC=\'browser_detect.js\'></script>\n<script type=\'text/javascript\' language=\'javascript\' SRC=\'/hvi?file=localization.js\'></script>\n<script type=\'text/javascript\' language=\'javascript\' SRC=\'javascript.js\'></script>\n\n<SCRIPT type="text/javascript" language=\'javascript\'>\n<!--\ndatapage = "cell1020.hvi";\n\nalert_msg = "Внутренняя ошибка: Неизвестный параметр";\n\n-->\n</SCRIPT>\n\n</head>\n\n<body onload="init()">\n\n<h1 id="title"></h1>\n<h2 id="title2"></h2>\n<div id="data"></div>\n\n<div id="comment" style="display: none;"></div>\n\n<div id="nav"></div>\n\n<div id="edit"></div>\n\n<div id="tijd"></div>\n\n<form name=\'settingstable\' method=\'POST\'>\n<input type=\'hidden\' name=\'edit_caption\' value=\'\'>\n<input type=\'hidden\' name=\'edit_line\' value=\'\'>\n<input type=\'hidden\' name=\'edit_label\' value=\'\'>\n<input type=\'hidden\' name=\'edit_par\' value=\'\'>\n<input type=\'hidden\' name=\'edit_format\' value=\'\'>\n<input type=\'hidden\' name=\'edit_file\' value=\'\'>\n<input type=\'hidden\' name=\'edit_mask\' value=\'\'>\n<input type=\'hidden\' name=\'edit_value\' value=\'\'>\n</form>\n\n</body>\n</html>\n']
    ok_alert = 'alert_msg = "";'
    res = asyncio.run(main())
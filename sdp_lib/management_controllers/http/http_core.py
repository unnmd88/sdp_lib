from typing import Callable, Any

import aiohttp

from sdp_lib.management_controllers.constants import Names
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.hosts_core import Host
from sdp_lib.management_controllers.http.request_sender import AsyncHttpRequests
from sdp_lib.management_controllers.parsers.parsers_peek_http_new import PeekWebPagesParser
from sdp_lib.management_controllers.structures import HttpResponseStructure
from sdp_lib.utils_common.utils_common import check_is_ipv4


class HttpHosts(Host):

    protocol = FieldsNames.protocol_http
    _parser_class: Callable

    def __init__(self, ipv4: str = None, host_id = None, session: aiohttp.ClientSession = None):
        super().__init__(ipv4=ipv4, host_id=host_id, driver=session)
        self._base_url = f'{Names.http_prefix}{self._ipv4}' if ipv4 is not None else ''
        # self.set_driver(session)
        self._request_sender = AsyncHttpRequests(session)
        self._request_method: Callable | None = None
        # self._parse_method_config = None
        self._request_response_get_states = None
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
        if self._tmp_response[HttpResponseStructure.ERROR] is not None:
            self._data_storage.put_errors(self._tmp_response[HttpResponseStructure.ERROR])
            return True
        return False

import asyncio

import aiohttp

from sdp_lib.management_controllers.exceptions import (
    ConnectionTimeout,
    BadControllerType
)
from sdp_lib.management_controllers.hosts_core import RequestResponse


class AsyncHttpRequests:

    default_timeout_get_request = .4
    default_timeout_post_request = .6

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._client_get_timeout = aiohttp.ClientTimeout(connect=self.default_timeout_get_request)
        self._client_post_timeout = aiohttp.ClientTimeout(connect=self.default_timeout_get_request)

    def load_session(self, session: aiohttp.ClientSession):
        self._session = session

    async def fetch(
            self,
            url: str,
            semaphore: asyncio.Semaphore,
            timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(connect=.4)
    ) -> tuple[str | None, int, str]:
        error = status = content = None
        try:
            async with semaphore:
                async with self._session.get(url, timeout=timeout) as response:
                    assert response.status == 200
                    status = response.status
                    content = await response.text()
        except asyncio.TimeoutError:
            error = ConnectionTimeout()
        except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
            error = BadControllerType()
        return error, status, content

    async def post_request(
            self,
            url: str,
            semaphore: asyncio.Semaphore,
            timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(connect=1),
            **kwargs
    ):
        error = status = content = None
        try:
            async with semaphore:
                async with self._session.post(url, timeout=timeout, **kwargs) as response:
                    assert response.status == 200
                    status = response.status
                    content = await response.text()
        except asyncio.TimeoutError:
            error = ConnectionTimeout()
        except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
            error = BadControllerType()
        return error, status, content

    async def common_request(
            self,
            request_response: RequestResponse
    ) -> RequestResponse:
        """
        Генерирует http запрос получения контента веб страницы.
        :return: Кортеж из 2 объектов:
                 [0] -> экземпляр производного класса от Exception
                 при ошибке в получении контента, иначе None.
                 [1] -> контент веб страницы типа str, если запрос выполнен успешно, иначе None.
        """
        error, status, content = await request_response.coro
        if error is not None:
            request_response.load_error(str(error))
        else:
            request_response.load_raw_response(content)
            request_response.load_status_response(status)
        return request_response





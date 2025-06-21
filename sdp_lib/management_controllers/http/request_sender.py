import asyncio
from typing import Callable

import aiohttp

from sdp_lib.management_controllers.exceptions import ConnectionTimeout, BadControllerType
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
    ) -> tuple[int, str]:

        async with semaphore:
            async with self._session.get(url, timeout=timeout) as response:
                assert response.status == 200
                content = await response.text()
                return response.status, content

    async def post_request(
            self,
            url: str,
            timeout: float = .8,
            **kwargs
    ) -> int:
        async with self._session.driver.post(
                url,
                timeout=aiohttp.ClientTimeout(connect=timeout),
                **kwargs
        ) as response:
            assert response.status == 200
            # print(f'response.status == {response.status}')
            return response.status

    # async def http_request_to_host(
    #         self,
    #         *,
    #         url: str,
    #         method: Callable,
    #         timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(connect=1),
    #         **kwargs
    # ) -> tuple[Exception | None, str | None]:
    #     """
    #     Генерирует http запрос получения контента веб страницы.
    #     :return: Кортеж из 2 объектов:
    #              [0] -> экземпляр производного класса от Exception
    #              при ошибке в получении контента, иначе None.
    #              [1] -> контент веб страницы типа str, если запрос выполнен успешно, иначе None.
    #     """
    #     # print(f'++ self.method: {method.__name__}')
    #     error = content = None
    #     try:
    #         content = await method(
    #             url=url,
    #             timeout=timeout,
    #             **kwargs
    #         )
    #     except asyncio.TimeoutError:
    #         error = ConnectionTimeout()
    #     except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
    #         error = BadControllerType()
    #     except aiohttp.client_exceptions.ClientConnectorError:
    #         error = ConnectionTimeout('from connector')
    #     return error, content


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
        # print(f'++ self.method: {method.__name__}')
        error = None
        try:
            status, content = await request_response.coro
            request_response.load_raw_response(content)
            request_response.load_status_response(status)
        except asyncio.TimeoutError:
            error = ConnectionTimeout()
        except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
            error = BadControllerType()
        except aiohttp.client_exceptions.ClientConnectorError:
            error = ConnectionTimeout('from connector')
        if error is not None:
            request_response.load_error(str(error))
        return request_response


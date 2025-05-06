import asyncio
from typing import Callable

import aiohttp

from sdp_lib.management_controllers.exceptions import ConnectionTimeout, BadControllerType


class AsyncHttpRequests:

    default_timeout_get_request = .4
    default_timeout_post_request = .6

    def __init__(self, instance_host):
        self._instance_host = instance_host

    async def fetch(
            self,
            url: str,
            timeout: float = .4
    ) -> str:
        async with self._instance_host.driver.get(url, timeout=aiohttp.ClientTimeout(connect=timeout)) as response:
            assert response.status == 200
            return await response.text()

    async def post_request(
            self,
            url: str,
            timeout: float = .8,
            **kwargs
    ) -> int:
        async with self._instance_host.driver.post(
                url,
                timeout=aiohttp.ClientTimeout(connect=timeout),
                **kwargs
        ) as response:
            assert response.status == 200
            # print(f'response.status == {response.status}')
            return response.status

    async def http_request_to_host(
            self,
            *,
            url: str,
            method: Callable,
            timeout: float = 1,
            **kwargs
    ) -> tuple[Exception | None, str | None]:
        """
        Генерирует http запрос получения контента веб страницы.
        :return: Кортеж из 2 объектов:
                 [0] -> экземпляр производного класса от Exception
                 при ошибке в получении контента, иначе None.
                 [1] -> контент веб страницы типа str, если запрос выполнен успешно, иначе None.
        """
        # print(f'++ self.method: {method.__name__}')
        error = content = None
        try:
            content = await method(
                url=url,
                timeout=timeout,
                **kwargs
            )
        except asyncio.TimeoutError:
            error = ConnectionTimeout()
        except (AssertionError, aiohttp.client_exceptions.ClientConnectorCertificateError):
            error = BadControllerType()
        except aiohttp.client_exceptions.ClientConnectorError:
            error = ConnectionTimeout('from connector')
        return error, content



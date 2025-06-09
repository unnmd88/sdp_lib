import asyncio
import os

import aiohttp
from dotenv import load_dotenv

from sdp_lib.management_controllers.exceptions import ConnectionTimeout, BadControllerType
from sdp_lib.management_controllers.http.http_core import HttpHost


load_dotenv()


class PeekWeb(HttpHost):

    cookies = {os.getenv('peek_web_k'): os.getenv('peek_web_v')}

    async def fetch(
            self,
            url: str,
            session: aiohttp.ClientSession,
            timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(connect=.6)
    ) -> str:
        async with session.get(url, timeout=timeout) as response:
            assert response.status == 200
            return await response.text()

    async def post(
            self,
            session: aiohttp.ClientSession,
            url: str,
            payload: dict[str, str],
            timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(connect=1)
    ) -> int:
        async with session.post(
                url,
                cookies=self.cookies,
                data=payload,
                timeout=timeout
        ) as response:
            assert response.status == 200
            print(f'response.status == {response.status}')
            return response.status
            print(f'response.status == {response.status}')
            print(f'response.host == {response.host_snmp}')
            print(f'response.ok == {response.ok}')
            print(f'response.ok == {response.history}')
            return await response.text()

    async def http_request_to_host(self, *, timeout: float = 1, **kwargs) -> tuple[Exception | None, str | None]:
        """
        Генерирует http запрос получения контента веб страницы.
        :return: Кортеж из 2 объектов:
                 [0] -> экземпляр производного класса от Exception
                 при ошибке в получении контента, иначе None.
                 [1] -> контент веб страницы типа str, если запрос выполнен успешно, иначе None.
        """
        print(f'++ self.method: {self.method.__name__}')
        error = content = None
        try:
            content = await self.method(
                url=self.full_url,
                session=self._driver,
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


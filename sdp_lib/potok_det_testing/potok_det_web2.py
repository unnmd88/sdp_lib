import asyncio
import os
from collections.abc import Container, Sequence

import httpx

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from httpx import Response

from sdp_lib.loggers.excel import ExcelLogger, DET_HEAD
from sdp_lib.observers.observers import BaseStateObserver

load_dotenv()


DET_STATE = -5


def create_observers_web_det_potok(
    ipv4: str,
    num_co: str,
    excel_log_filename: str,
    det_from_web: Sequence[Sequence],
    detectors_for_observe: Container[str] = None,
) -> Sequence[BaseStateObserver]:
    excel_logger = ExcelLogger(
        wb_name=excel_log_filename,
        sheet_name=f'{ipv4}_{num_co}',
        ip=ipv4,
        num_co=num_co,
        head=DET_HEAD,
    )
    _obs = []
    if detectors_for_observe is None:
        for det_data in det_from_web[1:]:
            _obs.append(BaseStateObserver(int(det_data[0]), name=f'D{int(det_data[0])}', excel_logger=excel_logger))
    else:
        for i, det_data in enumerate(det_from_web):
            if det_data[0] in detectors_for_observe:
                _obs.append(BaseStateObserver(i, name=f'D{det_data[0]}',excel_logger=excel_logger))
    return _obs


class PotokWebRoutes:

    protocol_prefix: str = 'https://'

    def __init__(self, ipv4: str):
        self.ipv4 = ipv4
        self.login = self.protocol_prefix + self.ipv4 + '/login'
        self.main = self.protocol_prefix + self.ipv4 + '/index'
        self.detectors = self.protocol_prefix + self.ipv4 + '/detectors'


class PotokWeb:

    user_agent = os.getenv('user_agent')
    login_data = {
        "login": os.getenv('POTOK_WEB_LOGIN'),
        "password": os.getenv('POTOK_WEB_PASSWORD'),
        "csrf_token": "",
    }

    def __init__(self, client, ipv4):
        self.client = client
        self.ipv4 = ipv4
        self.routes = PotokWebRoutes(ipv4)

    async def login(self):
        response = await self.client.get(self.routes.login)
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf_token"})["value"]
        self.login_data['csrf_token'] = csrf_token
        res: Response = await self.client.post(self.routes.login, data=self.login_data, follow_redirects=True)
        print(f'res: {res.text}')

    async def get_det_detectors(self):
        try:
            response = await self.client.get(self.routes.detectors, timeout=3)
            if response.status_code != 200:
                return None
        except (httpx.ReadTimeout, httpx.ConnectTimeout):
            return None
        return tuple(det_data.text.split() for det_data in BeautifulSoup(response.text, "html.parser").find_all('tr'))


async def main(timeout: float = 1):
    ipv4 = '10.179.72.97'
    num_co = '190'
    client = httpx.AsyncClient(verify=False, max_redirects=20, headers={"user-agent": os.getenv('user_agent')})
    potok_web = PotokWeb(client, ipv4)
    try:
        await potok_web.login()
        detectors = await potok_web.get_det_detectors()
        _observers = create_observers_web_det_potok(
            ipv4, num_co,
            'PotokWebDet_log_v2.xlsx',
            detectors,
            {'28', '29'}
        )
        print(detectors)
        print('-' * 100)
        print(_observers)
        while True:
            detectors = await potok_web.get_det_detectors() # (['1', '1', 'DTR', '0', 'Не', 'занят', 'Занят', 'Нормальный'], ...)
            for obs in _observers:
                obs.check_is_switched_and_write_log(detectors[obs.position][DET_STATE])
            await asyncio.sleep(timeout)
    finally:
        await client.aclose()


if __name__ == '__main__':
    asyncio.run(main())


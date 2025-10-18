import asyncio
import json
import textwrap
import time

import aiohttp
import httpx
import requests
from aiohttp import ClientConnectorCertificateError, FormData
from bs4 import BeautifulSoup

from excel_logs import ExcelLogger, DET_HEAD
from sdp_lib.management_controllers.snmp.snmp_utils import PrettyVsnString
from observers import BaseSwitchStateObserver
from sdp_lib.management_controllers.snmp.oids import Oids

from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity


from sdp_lib.management_controllers.snmp.snmp_api import PotokP
from sdp_lib.management_controllers.snmp.snmp_requests import snmp_engine


# async def post(ipv4, session: aiohttp.ClientSession):
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#         "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
#     }
#     headers1 = {
#         "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
#     }
#     # url = f'https://{ipv4}/login'
#
#     url = f'https://10.45.154.12/login'
#
#
#
#     r = await session.get(headers=headers1, url=url)
#
#     soup = BeautifulSoup(await r.text(), "html.parser")
#     csrf_token = soup.find("input", {"name": "csrf_token"})["value"]
#     print(f'csrf_token: {csrf_token}')
#     data = {
#         "login": "operator",
#         "password": "operator",
#         "csrf_token": csrf_token,
#     }
#     async with session.post(headers=headers, url=url, data=json.dumps(data)) as resp:
#         res = await resp.text()
#         print(res)


# async def post2(ipv4):
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
#     }
#     headers1 = {
#         "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
#     }
#     url = f'https://{ipv4}/login'
#
#     # url = f'https://10.45.154.12/login'
#
#     async with httpx.AsyncClient(verify=False, max_redirects=20, headers=headers1) as client:
#
#         response = await client.get(url)
#
#         soup = BeautifulSoup(response.text, "html.parser")
#         csrf_token = soup.find("input", {"name": "csrf_token"})["value"]
#         print(f'csrf_token: {csrf_token}')
#         data = {
#             "login": "admin",
#             "password": "zBCTRuV7",
#             "csrf_token": csrf_token,
#         }
#         res = await client.post(url, data=data, follow_redirects=True)
#         print(client.headers)
#         print('after post login')
#         print(f'res: {res.text}')
#         response = await client.get(f'https://{ipv4}/detectors')
#         print(response.status_code)
#         print(response.headers)
#         soup = BeautifulSoup(response.text, "html.parser")
#         # print(soup.find_all('tr'))
#         for i, line in enumerate(soup.find_all('tr')):
#             print(f'i: {i}, line:{line}')
#             print(f'i_text: {i}, line:{line.text}')
#             print(f'i_text_spit: {i}, line:{line.text.split()}')
#     # async with session.post(headers=headers, url=url, data=json.dumps(data)) as resp:
#     #     res = await resp.text()
#     #     print(res)


async def post2(client, ipv4):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }
    headers1 = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }
    url = f'https://{ipv4}/login'

    # url = f'https://10.45.154.12/login'

    response = await client.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "csrf_token"})["value"]
    print(f'csrf_token: {csrf_token}')
    data = {
        "login": "admin",
        "password": "zBCTRuV7",
        "csrf_token": csrf_token,
    }
    res = await client.post(url, data=data, follow_redirects=True)
    print(client.headers)
    print('after post login')
    print(f'res: {res.text}')
    response = await client.get(f'https://{ipv4}/detectors')
    print(response.status_code)
    print(response.headers)
    soup = BeautifulSoup(response.text, "html.parser")
    # print(soup.find_all('tr'))
    for i, line in enumerate(soup.find_all('tr')):
        print(f'i: {i}, line:{line}')
        print(f'i_text: {i}, line:{line.text}')
        print(f'i_text_spit: {i}, line:{line.text.split()}')


    # async with session.post(headers=headers, url=url, data=json.dumps(data)) as resp:
    #     res = await resp.text()
    #     print(res)


async def get_det(client: httpx.AsyncClient, ipv4):
    try:
        response = await client.get(f'https://{ipv4}/detectors', timeout=2)
        if response.status_code != 200:
            return None, None
        # print(response.status_code)
    except (httpx.ReadTimeout, httpx.ConnectTimeout):
        return None, None

    soup = BeautifulSoup(response.text, "html.parser")
    all_tr = soup.find_all('tr')
    return all_tr[1].text.split()[-5],  all_tr[2].text.split()[-5],
    for i, line in enumerate(soup.find_all('tr')):
        print(f'i_text_spit: {i}, line:{line.text.split()}')



# async def fetch(ipv4, session: aiohttp.ClientSession):
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#         "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
#     }
#     # url = f'https://{ipv4}/login'
#
#     url = f'https://10.45.154.12/login'
#     async with session.get(headers=headers, url=url) as resp:
#         res = await resp.text()
#         print(res)



# def sync_post(ipv4):
#     ipv4 = '10.45.154.12'
#     headers = {
#         "Content-Type": "application/x-www-form-urlencoded",
#         "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
#     }
#     url = f'https://{ipv4}/login'
#     url2= f'https://{ipv4}/index'
#
#
#     with requests.Session() as s:
#         response = s.get(url, verify=False)
#         soup = BeautifulSoup(response.text, "html.parser")
#         csrf_token = soup.find("input", {"name": "csrf_token"})["value"]
#         data = {
#             "login": "admin",
#             "password": "zBCTRuV7",
#             "csrf_token": csrf_token,
#         }
#         r = s.post(url=url, data=data, headers=headers, verify=False)
#         print(r.text)
#         r = s.get(url=url2, verify=False)
#         print(r.text)


async def main(timeout: float = 1):
    ipv4 = '10.179.72.97'

    excel_logger = ExcelLogger(
        wb_name='PotokWebDet_log.xlsx',
        sheet_name=f'{ipv4}_CO190',
        ip=ipv4,
        num_co='CO190',
        head=DET_HEAD,

    )
    observer1 = BaseSwitchStateObserver('1', name='D28(D1)', excel_logger=excel_logger)
    observer2 = BaseSwitchStateObserver('1', name='D29(D2)', excel_logger=excel_logger)
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }
    client = httpx.AsyncClient(verify=False, max_redirects=20, headers=headers)
    try:
        await post2(client, ipv4)
        while True:
            d1, d2 = await get_det(client, ipv4)
            observer1.check_and_write_log(d1)
            observer2.check_and_write_log(d2)
            await asyncio.sleep(timeout)
    finally:
        await client.aclose()


if __name__ == '__main__':
    asyncio.run(main())


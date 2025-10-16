import asyncio
import json
import textwrap
import time

import aiohttp
import httpx
import requests
from aiohttp import ClientConnectorCertificateError, FormData
from bs4 import BeautifulSoup

from sdp_lib.management_controllers.snmp.snmp_utils import PrettyVsnString
from observers import BaseSwitchStateObserver
from sdp_lib.management_controllers.snmp.oids import Oids

from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity


from sdp_lib.management_controllers.snmp.snmp_api import PotokP
from sdp_lib.management_controllers.snmp.snmp_requests import snmp_engine


async def post(ipv4, session: aiohttp.ClientSession):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
    }
    headers1 = {
        "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
    }
    # url = f'https://{ipv4}/login'

    url = f'https://10.45.154.12/login'



    r = await session.get(headers=headers1, url=url)

    soup = BeautifulSoup(await r.text(), "html.parser")
    csrf_token = soup.find("input", {"name": "csrf_token"})["value"]
    print(f'csrf_token: {csrf_token}')
    data = {
        "login": "operator",
        "password": "operator",
        "csrf_token": csrf_token,
    }
    async with session.post(headers=headers, url=url, data=json.dumps(data)) as resp:
        res = await resp.text()
        print(res)


async def post2(ipv4):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }
    headers1 = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"

    }
    url = f'https://{ipv4}/login'

    # url = f'https://10.45.154.12/login'

    async with httpx.AsyncClient(verify=False, max_redirects=20, headers=headers1) as client:

        response = await client.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf_token"})["value"]
        print(f'csrf_token: {csrf_token}')
        data = {
            "login": "",
            "password": "",
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


async def fetch(ipv4, session: aiohttp.ClientSession):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
    }
    # url = f'https://{ipv4}/login'

    url = f'https://10.45.154.12/login'
    async with session.get(headers=headers, url=url) as resp:
        res = await resp.text()
        print(res)



def sync_post(ipv4):
    ipv4 = '10.45.154.12'
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
    }
    url = f'https://{ipv4}/login'
    url2= f'https://{ipv4}/index'


    with requests.Session() as s:
        response = s.get(url, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf_token"})["value"]
        data = {
            "login": "admin",
            "password": "zBCTRuV7",
            "csrf_token": csrf_token,
        }
        r = s.post(url=url, data=data, headers=headers, verify=False)
        print(r.text)
        r = s.get(url=url2, verify=False)
        print(r.text)


async def main(timeout: float = 3):
    ipv4 = '10.179.72.97'

    snmp_host = PotokP(ipv4=ipv4, engine=snmp_engine, host_id='190')
    await snmp_host.get_scn_from_host_and_set_to_attr()
    print(f'host ip: {snmp_host.ip_v4}')
    print(f'host id: {snmp_host.host_id}')
    print(f'scn from host as chars: {snmp_host.scn.scn_as_chars}')
    print(f'scn from host as ASCII: {snmp_host.scn.scn_as_ascii}')

    samples = await snmp_host.request_sender.snmp_get([ObjectType(ObjectIdentity('.1.3.6.1.4.1.13267.3.2.2.5.0'))])
    print(f'Samples: {samples[3][0][1].prettyPrint()}')
    pretty_vsn = PrettyVsnString(int(samples[3][0][1].prettyPrint()))
    det_cnt = await snmp_host.request_sender.snmp_get([ObjectType(ObjectIdentity(Oids.utcType2ScootDetectorCount + snmp_host.scn.scn_as_ascii))])
    print(f'NumDetectors: {det_cnt[3][0][1].prettyPrint()}')

    _oids = [Oids.utcReplyVSn + snmp_host.scn.scn_as_ascii,]
    observer = BaseSwitchStateObserver('1')

    while True:
        try:
            res = await snmp_host.request_sender.snmp_get([ObjectType(ObjectIdentity(oid)) for oid in _oids])
            octet_string_vsn = res[3][0][1].prettyPrint()
            # print(f'OctStr: {octet_string_vsn}')
            print(f'PrettyOctStr: {pretty_vsn.get_pretty_string(octet_string_vsn)}')
            observer.check_on(octet_string_vsn[2])
            print(f'observer: {observer._switch_points}')
        except IndexError:
            print('Controller is unavailable')
        await asyncio.sleep(timeout)



if __name__ == '__main__':
    asyncio.run(main())


# import asyncio
# import os
# import time
#
# import aiohttp
# from dotenv import load_dotenv
#
# from pysnmp.hlapi.asyncio import *
# from sdp_lib.management_controllers import controller_management2, controller_management
# from sdp_lib.management_controllers.snmp_oids import Oids
# from sdp_lib.utils_common import write_data_to_file
#
# load_dotenv()
#
# def oupt_snmp_data(data):
#     vals = {}
#     for oid, val in data:
#         print(f'oid: {str(oid)}, val: {str(val)}')
#         vals[f'{Oids(str(oid)).name}[{str(oid)}]'] = val.prettyPrint()
#
#     print(vals)
#
# ip = '10.122.38.3'
#
# host_id = 'test_laba'
#
# headers = {
#     'User-Agent': os.getenv('user_agent')
# }
#
# #Peek
# ROUTE_GET_INPUTS = os.getenv('ROUTE_GET_INPUTS')
# #Swarco
# ROUTE_MAIN = os.getenv('ROUTE_MAIN')
# ROUTE_DISPLAY = os.getenv('ROUTE_DISPLAY')
#
# url_413 = f'http://10.122.38.3{ROUTE_GET_INPUTS}'
# ip510 = f'10.179.64.25'
# co510_display = f'http://10.179.64.25{ROUTE_DISPLAY}'
#
# async def fetch(ipv4: str, session: aiohttp.ClientSession, timeout: float = 4):
#     url = f'http://{ipv4}{ROUTE_GET_INPUTS}'
#     async with session.get(url, timeout=timeout) as responce:
#         if responce.status != 200:
#             raise TypeError()
#         r = await responce.text()
#         print(r)
#         return r
#
# async def get_content(ipv4: str, session: aiohttp.ClientSession, timeout: float = 4):
#     payload = {
#         os.getenv('k1_swarco_web'): os.getenv('k2_swarco_web'),
#         os.getenv('k3_swarco_web'): os.getenv('k4_swarco_web'),
#         os.getenv('k5_swarco_web'): os.getenv('k6_swarco_web'),
#         os.getenv('k7_swarco_web'): os.getenv('k8_swarco_web'),
#     }
#
#     async with session.post(f'http://{ipv4}{ROUTE_MAIN}',
#                             headers=headers, timeout=timeout,data=payload) as r:
#         await r.read()
#         session.cookie_jar.update_cookies(r.cookies)
#     async with session.get(f'http://{ipv4}{ROUTE_DISPLAY}',
#                            timeout=timeout) as r:
#         content = await r.text()
#         print(content)
#
# async def main():
#
#     async with aiohttp.ClientSession() as session:
#         hosts_swarco = ['10.179.65.17', '10.179.64.177', ]
#         hosts_peek = ['10.122.38.3']
#         start_time = time.time()
#         swarco = [asyncio.create_task(get_content(host, session)) for host in hosts_swarco]
#         peek = [asyncio.create_task(fetch(host, session)) for host in hosts_peek]
#         res = await asyncio.gather(*[coro for coro in swarco + peek])
#
#         print(f'Время выполнения: {time.time() - start_time}')
# asyncio.run(main())
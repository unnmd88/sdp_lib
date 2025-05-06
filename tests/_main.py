import asyncio

import aiohttp
from pysnmp.entity.engine import SnmpEngine

# from sdp_lib.management_controllers.http.peek import peek_http
# from sdp_lib.management_controllers.snmp import snmp_api
from sdp_lib.management_controllers import api


async def main():

    try:
        a_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(1))
        obj1 = api.SwarcoStcip(ipv4='10.179.14.185')
        obj2 = api.PotokP(ipv4='10.179.63.241')
        obj3 = api.PotokS(ipv4='10.179.65.153')
        obj4 = api.PeekWebHosts(ipv4='10.179.59.9', session=a_session)
        objs = [obj1, obj2, obj3, obj4]
        res = await asyncio.gather(*(ob.get_states() for ob in objs))
        for r in res:
            print(r)
            print('----------')
            print(r.response_as_dict)
    finally:
        await a_session.close()


if __name__ == '__main__':
    asyncio.run(main())
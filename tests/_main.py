import asyncio

import aiohttp
from pysnmp.entity.engine import SnmpEngine

# from sdp_lib.management_controllers.http.peek import peek_http
# from sdp_lib.management_controllers.snmp import snmp_api
from sdp_lib.management_controllers import api


async def get_states(session=None):

    obj1 = api.SwarcoStcip(ipv4='10.179.14.185')
    obj2 = api.PotokP(ipv4='10.179.63.241')
    obj3 = api.PotokS(ipv4='10.179.65.153')
    obj4 = api.PeekWebHosts(ipv4='10.179.59.9', session=session)
    objs = [obj1, obj2, obj3, obj4]
    res = await asyncio.gather(*(ob.get_states() for ob in objs))
    for r in res:
        print(r)
        print('----------')
        print(r.response_as_dict)
    return res

async def set_stage_swarco(ip='10.179.14.185', val=0):
    ob = api.SwarcoStcip(ipv4=ip)
    await ob.set_stage(val)
    return ob

async def get_curr_stage(session=None):
    obj3 = api.PotokS(ipv4='10.179.65.153')
    res= await obj3.get_current_stage()
    print(res)
    print("*" * 100)
    print(obj3.currentstage)
    print(obj3.last_response)
    return res


async def main():
    a_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(1))
    try:
        # await get_curr_stage()
        await get_states(session=a_session)
    finally:
        await a_session.close()



if __name__ == '__main__':
    asyncio.run(main())
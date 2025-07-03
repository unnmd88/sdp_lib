import asyncio
import json
import time

import aiohttp

from sdp_lib.management_controllers.api import *



async def main():
    timeout = aiohttp.ClientTimeout(1)
    sess = aiohttp.ClientSession(timeout=timeout)

    obj = PeekWebHosts(ipv4='10.45.154.19', host_id='laba', session=sess)
    obj = PeekUg405(ipv4='10.45.154.19', host_id='laba', engine=snmp_engine)
    obj = PotokS(ipv4='10.179.88.113', host_id='3281')
    obj = PotokS(ipv4='10.179.24.153', host_id='205', engine=snmp_engine)
    obj = SwarcoStcip(ipv4='10.179.61.33', host_id='3205', engine=snmp_engine)

    try:
        # start_time = time.time()
        # res = await obj.set_stage(2)
        # res = await obj.get_states()
        while True:
            start_time = time.time()
            res = await obj.get_states()
            # res = await obj.set_stage(5)
            print(json.dumps(res.build_response_as_dict(), indent=4, ensure_ascii=False))
            print(f'время составло: {time.time() - start_time}')
            await asyncio.sleep(2)
    finally:
        await sess.close()

    # print(obj.response_as_dict)
    # print(json.dumps(obj.response_as_dict, indent=4))


    """set command test"""


    # print(res.response_as_dict)

    print(res)
    print(res.response)
    print(res.ip_v4)
    print(f'время составло: {time.time() - start_time}')

    return obj.response


if __name__ == '__main__':

    asyncio.run(main())
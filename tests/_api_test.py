import asyncio
import time

import aiohttp

from sdp_lib.management_controllers.api import *



async def main():
    timeout = aiohttp.ClientTimeout(1)
    sess = aiohttp.ClientSession(timeout=timeout)


    obj = PotokS(ipv4='10.179.88.113', host_id='3281')
    # obj = SwarcoStcip(ip_v4='10.179.20.129')
    # obj = SwarcoStcip(ip_v4='10.179.68.105')
    # obj = SwarcoStcip(ip_v4='10.179.57.1')
    # obj = SwarcoStcip(ip_v4='10.179.61.33', host_id='3205')
    # obj = PotokS(ip_v4='10.179.68.177',)
    # obj = SwarcoStcip(ipv4='10.179.108.177', host_id='2851', engine=SnmpEngine())

    # obj = PotokP(ip_v4='10.179.69.65', host_id='2600')
    # obj = PotokP(ip_v4='10.179.56.105', host_id='155')
    # obj = PotokP(ipv4='10.179.108.129', host_id='2822')
    obj = PotokP(ipv4='10.179.69.129', host_id='2954', engine=snmp_engine)
    # obj = PotokS(ipv4='10.179.24.153', host_id='205', engine=snmp_engine)
    # obj.set_driver()
    # obj = SwarcoStcip(ipv4='10.179.89.225', host_id='3584')

    # obj.ip_v4 = '10.179.20.129'

    # obj = PeekUg405(ipv4='10.179.67.73')

    # obj = SwarcoStcip(ipv4='10.179.20.129', engine=snmp_engine, host_id='2405')

    # obj = PeekUg405(ipv4='10.45.154.19', host_id='laba', engine=snmp_engine)

    obj = PeekWebHosts('10.45.154.19', session=sess)

    # start_time = time.time()
    # res = await obj.set_stage(2)

    try:
        # start_time = time.time()
        # res = await obj.set_stage(2)
        # res = await obj.get_states()

        while True:
            start_time = time.time()
            res = await obj.get_states()
            # res = await obj.set_stage(5)
            print(res.response)
            print(res.response.build_response_as_dict_from_raw_data_responses(res.ip_v4))
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
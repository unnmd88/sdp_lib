import asyncio

from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.snmp import snmp_api


async def main():
    obj1 =  snmp_api.SwarcoStcip(ipv4='10.179.14.185')
    obj2 =  snmp_api.PotokP(ipv4='10.179.63.241')
    obj3 =  snmp_api.PotokS(ipv4='10.179.65.153')

    await obj1.get_states()
    print(obj1)
    print('----------')
    print(obj1.response_as_dict)
    print('----------')
    print(obj1.last_response[3])

    await obj2.get_states()
    print(obj2)
    print(obj2.scn_as_ascii_string)
    print(obj2.scn_as_chars)
    print('----------')
    print(obj2.response_as_dict)
    print('----------')
    print(obj2.last_response[3])
    #
    # await obj3.get_states()
    # print(obj3)
    # print('----------')
    # print(obj3.response_as_dict)
    # print('----------')
    # print(obj3.last_response[3])

    # await obj2.set_stage(0)



if __name__ == '__main__':
    asyncio.run(main())
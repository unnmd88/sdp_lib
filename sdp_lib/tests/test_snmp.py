import asyncio

from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.snmp import snmp_api



async def main():
    obj =  snmp_api.SwarcoStcip(ipv4='10.179.14.185', engine=SnmpEngine())
    await obj.get_states()
    print(obj)
    print()



if __name__ == '__main__':
    asyncio.run(main())
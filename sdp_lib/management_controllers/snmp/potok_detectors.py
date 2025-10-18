import asyncio

from management_controllers.snmp.oids import Oids

from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity


from sdp_lib.management_controllers.snmp.snmp_api import PotokP
from sdp_lib.management_controllers.snmp.snmp_requests import snmp_engine


async def main(timeout: float = 1):
    snmp_host = PotokP(ipv4='10.179.72.97', engine=snmp_engine, host_id='190')
    await snmp_host.get_scn_from_host_and_set_to_attr()
    print(f'host ip: {snmp_host.ip_v4}')
    print(f'host id: {snmp_host.host_id}')
    print(f'scn from host as chars: {snmp_host.scn.scn_as_chars}')
    print(f'scn from host as ASCII: {snmp_host.scn.scn_as_ascii}')

    _oids = [Oids.utcReplyVSn + snmp_host.scn.scn_as_ascii,]

    while True:
        try:
            res = await snmp_host.request_sender.snmp_get([ObjectType(ObjectIdentity(oid)) for oid in _oids])
            print(f'OctStr: {res[3][0][1].prettyPrint()}')
            # print(f'CntDet: {res[3][1][1].prettyPrint()}')
        except IndexError:
            print('Controller is unavailable')
        # except Exception as e:
        #     print(e)
        await asyncio.sleep(timeout)


if __name__ == '__main__':
    asyncio.run(main())


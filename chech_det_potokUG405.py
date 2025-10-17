import asyncio

from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.snmp_core import PotokP
from sdp_lib.management_controllers.snmp.snmp_requests import snmp_engine
from sdp_lib.management_controllers.snmp.snmp_utils import PrettyVsnString

p = ''
async def main():
    ipv4 = '10.179.12.185'
    snmp_host = PotokP(ipv4=ipv4, engine=snmp_engine)
    await snmp_host.get_scn_from_host_and_set_to_attr()
    print(f'host ip: {snmp_host.ip_v4}')
    print(f'host id: {snmp_host.host_id}')
    print(f'scn from host as chars: {snmp_host.scn.scn_as_chars}')
    print(f'scn from host as ASCII: {snmp_host.scn.scn_as_ascii}')

    det_cnt = await snmp_host.request_sender.snmp_get([ObjectType(ObjectIdentity(Oids.utcType2ScootDetectorCount + snmp_host.scn.scn_as_ascii))])
    print(f'NumDetectors: {det_cnt[3][0][1].prettyPrint()}')

    samples = await snmp_host.request_sender.snmp_get([ObjectType(ObjectIdentity('.1.3.6.1.4.1.13267.3.2.2.5.0'))])
    samples_string = samples[3][0][1].prettyPrint()
    print(f'Samples: {samples_string}')
    vsn = await snmp_host.request_sender.snmp_get([ObjectType(ObjectIdentity(Oids.utcReplyVSn + snmp_host.scn.scn_as_ascii))])
    octet_string_vsn = vsn[3][0][1].prettyPrint()
    pretty_vsn = PrettyVsnString(int(det_cnt[3][0][1].prettyPrint()))
    print(f'Длина Vsn строки: {len(octet_string_vsn[2:])}')
    print(f'Длина сырой octet_string_vsn Vsn строки: {len(octet_string_vsn)}')
    print(f'Vsn строка: {octet_string_vsn}')


if __name__ == '__main__':
    asyncio.run(main())
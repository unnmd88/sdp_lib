import asyncio

from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.snmp_core import PotokP
from sdp_lib.management_controllers.snmp.snmp_requests import snmp_engine
from sdp_lib.management_controllers.snmp.snmp_utils import PrettyVsnString
from observers import BaseSwitchStateObserver
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('{name} [{levelname:^11}] {asctime} {message}', style='{')
file_handler = logging.FileHandler('vsn.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)



async def main(timeout: float = 1):
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
    observer1 = BaseSwitchStateObserver('1')
    observer2 = BaseSwitchStateObserver('1')
    try:
        while True:
            try:
                res = await snmp_host.request_sender.snmp_get([ObjectType(ObjectIdentity(oid)) for oid in _oids])
                octet_string_vsn = res[3][0][1].prettyPrint()
                # print(f'OctStr: {octet_string_vsn}')
                print(f'PrettyOctStr: {pretty_vsn.get_pretty_string(octet_string_vsn)}')
                observer1.check(octet_string_vsn[3])
                observer2.check(octet_string_vsn[2])
                print(f'observerD1: {observer1._online}')
                print(f'observerD2: {observer2._online}')
                await asyncio.sleep(timeout)

            except IndexError:
                print('Controller is unavailable')

    finally:
        print('D1 Online')
        for el in observer1._online:
            logger.info(el.duration)
            # print(el)
        print('D1 Offline')
        for el in observer1._offline:
            # print(el)
            logger.info(el.duration)







if __name__ == '__main__':
    asyncio.run(main())
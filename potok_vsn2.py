import asyncio
import logging
from collections.abc import Sequence, Collection

from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from excel_logs import ExcelLogger, DET_HEAD
from observers2 import BaseStateObserver
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.snmp_core import PotokP
from sdp_lib.management_controllers.snmp.snmp_requests import snmp_engine
from sdp_lib.management_controllers.snmp.snmp_utils import PrettyVsnString


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('{name} [{levelname:^11}] {asctime} {message}', style='{')
file_handler = logging.FileHandler('vsn2.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def create_observers_vsn(
    num_det: int,
    ipv4, num_co,
    num_det_to_observe: Collection[int] = None
) -> Sequence[BaseStateObserver]:
    excel_logger = ExcelLogger(
        wb_name='utcReplyVSn_log_v2.xlsx',
        sheet_name=f'{ipv4}_{num_co}',
        ip=ipv4,
        num_co=num_co,
        head=DET_HEAD
    )
    _observers = []
    for det in range(num_det):
        if num_det_to_observe is not None and (det + 1 in num_det_to_observe):
            if det % 2 == 0:
                i = det + 1
            else:
                i = det - 1
            _observers.append(BaseStateObserver(i, name=f'D{det + 1}', excel_logger=excel_logger))
    return _observers


async def main(timeout: float = .8):

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
    num_det = int(det_cnt[3][0][1].prettyPrint())
    print(f'NumDetectors: {num_det}')

    _oids = [ObjectType(ObjectIdentity(Oids.utcReplyVSn + snmp_host.scn.scn_as_ascii))]

    _observers = create_observers_vsn(num_det, ipv4=ipv4, num_co=snmp_host.scn.scn_as_chars, num_det_to_observe={1, 2})
    try:
        while True:
            err_indication, err_status, err_index, varbinds = await snmp_host.request_sender.snmp_get(
                _oids,
                timeout=.6,
            )
            if err_indication or not varbinds:
                for obs in _observers:
                    obs.check_and_write_log(None)
            else:
                octet_string_vsn = varbinds[0][1].prettyPrint()
                print(f'PrettyOctStr: {pretty_vsn.get_pretty_string(octet_string_vsn)}')
                for obs in _observers:
                    obs.check_and_write_log(octet_string_vsn[2 + obs.position])
            await asyncio.sleep(timeout)
    except TypeError as e:
        logger.critical('FAIL!!!! ' + e)


if __name__ == '__main__':

    asyncio.run(main())




import asyncio
import time

from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from sdp_lib.management_controllers.snmp import snmp_utils
from sdp_lib.management_controllers.snmp.oids import oids_scn_required, Oids
from sdp_lib.management_controllers.snmp.snmp_core import (
    SwarcoStcip,
    PotokP,
    PotokS,
    PeekUg405
)
from sdp_lib.management_controllers.snmp.snmp_requests import snmp_engine


async def main(timeout: float = 0.1):



    host = PotokP(ipv4='10.45.154.12', engine=snmp_engine)
    await host.get_scn_from_host_and_set_to_attr()
    # _oids = [ObjectType(ObjectIdentity(oid)) for oid in [Oids.utcReplyGn, Oids.potokP_utcReplyPromTact]]
    _oids = [
        Oids.utcReplyGn + host.scn.scn_as_ascii,
        Oids.potokP_utcReplyPromTact + host.scn.scn_as_ascii
    ]

    print(f'SCN WAS SET: {host.scn.scn_as_ascii}')

    res = await host.request_sender.snmp_get([ObjectType(ObjectIdentity(oid)) for oid in _oids])

    prev_stage_as_hex = res[3][0][1].prettyPrint()
    prev_stage_as_int = snmp_utils.convert_val_as_hex_to_decimal(prev_stage_as_hex)


    prev_prom_as_hex = res[3][1][1].prettyPrint()
    prev_prom_as_int = snmp_utils.convert_val_as_hex_to_decimal(prev_prom_as_hex)


    tmr1 = time.perf_counter()

    while True:
        err_indication, err_status, err_index, varbinds = await host.request_sender.snmp_get(
            [ObjectType(ObjectIdentity(oid)) for oid in _oids]
        )
        # stg = f'{res[3][0][0]}(Stage)={res[3][0][1].prettyPrint()}({snmp_utils.convert_val_as_hex_to_decimal(res[3][0][1].prettyPrint())})'
        # prom = f'{res[3][1][0]}(Prom)={res[3][1][1].prettyPrint()}({snmp_utils.convert_val_as_hex_to_decimal(res[3][1][1].prettyPrint())})'
        if varbinds:
            curr_stage_as_hex = varbinds[0][1].prettyPrint()
            curr_prom_as_hex = varbinds[1][1].prettyPrint()

            curr_stage_as_int = snmp_utils.convert_val_as_hex_to_decimal(curr_stage_as_hex)
            curr_prom_as_int = snmp_utils.convert_val_as_hex_to_decimal(curr_prom_as_hex)

            # print(f'{curr_prom_as_hex=} {curr_prom_as_int=}')
            if prev_prom_as_hex != curr_prom_as_hex:
                duration = time.perf_counter() - tmr1
                tmr1 = time.perf_counter()
                print(f'stg={prev_stage_as_hex}({prev_stage_as_int}) prom={prev_prom_as_hex}({prev_prom_as_int}) | duration={duration}')
            prev_stage_as_hex = curr_stage_as_hex
            prev_stage_as_int = snmp_utils.convert_val_as_hex_to_decimal(prev_stage_as_hex)
            prev_prom_as_hex = curr_prom_as_hex
            prev_prom_as_int = snmp_utils.convert_val_as_hex_to_decimal(prev_prom_as_hex)
        await asyncio.sleep(timeout)


if __name__ == '__main__':

    asyncio.run(main())
import asyncio

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



    # host = PotokP('10.45.154.12')
    host = PotokP(ipv4='10.45.154.12', engine=snmp_engine)
    await host.get_scn_from_host_and_set_to_attr()
    # _oids = [ObjectType(ObjectIdentity(oid)) for oid in [Oids.utcReplyGn, Oids.potokP_utcReplyPromTact]]
    _oids = [
        Oids.utcReplyGn + host.scn.scn_as_ascii,
        Oids.potokP_utcReplyPromTact + host.scn.scn_as_ascii
    ]
    print(_oids)

    print(f'SCN WAS SET: {host.scn.scn_as_ascii}')
    # res = await host.request_sender.snmp_get(
    #     [ObjectType(ObjectIdentity(oid)) for oid in _oids]
    # )

    # for oid, val in res[3]:
    #     print(f'oid: {oid}, val: {val.prettyPrint()}')


    while True:
        res = await host.request_sender.snmp_get(
            [ObjectType(ObjectIdentity(oid)) for oid in _oids]
        )
        stg = f'{res[3][0][0]}(Stage)={res[3][0][1].prettyPrint()}({snmp_utils.convert_val_as_hex_to_decimal(res[3][0][1].prettyPrint())})'
        prom = f'{res[3][1][0]}(Prom)={res[3][1][1].prettyPrint()}({snmp_utils.convert_val_as_hex_to_decimal(res[3][1][1].prettyPrint())})'
        print(stg, prom, sep='\n')
        await asyncio.sleep(timeout)


if __name__ == '__main__':

    asyncio.run(main(1))
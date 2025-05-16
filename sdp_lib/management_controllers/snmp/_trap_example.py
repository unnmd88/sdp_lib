import datetime
from enum import StrEnum

from pysnmp.carrier.asyncio.dispatch import AsyncioDispatcher
from pysnmp.carrier.asyncio.dgram import udp, udp6
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
import logging
from sdp_lib.management_controllers.snmp import oids
from sdp_lib.management_controllers.snmp import snmp_utils

import logging_config




class ExtraOids(StrEnum):

    time_ticks = '1.3.6.1.2.1.1.3.0'





class Fields(StrEnum):
    current_time_ticks = 'current_time_ticks'
    last_time_ticks = 'last_time_ticks'
    time_delta = 'time_delta'
    stage_val = 'stage_val'
    stage_num = 'stage_number'


field_names_from_oid = {
    ExtraOids.time_ticks: ExtraOids.time_ticks,
    oids.Oids.swarcoUTCTrafftechPhaseStatus: Fields.stage_val
}

aw_oids = {oids.Oids.swarcoUTCTrafftechPhaseStatus, ExtraOids.time_ticks}

last_time_ticks = [0]


def get_varbinds_as_dict(varbinds) -> dict[str, int | str] | None:

    data = {}

    for oid, val in varbinds:
        oid_as_str = str(oid)
        val_as_str = str(val)

        if oid_as_str in aw_oids:
            if oid_as_str == ExtraOids.time_ticks:
                val_as_int = int(val_as_str)
                data[Fields.current_time_ticks] = val_as_int
            elif oid_as_str == oids.Oids.swarcoUTCTrafftechPhaseStatus:
                data[Fields.stage_val] = val_as_str
                data[Fields.stage_num] = snmp_utils.StageConverterMixinPotokS.get_num_stage_from_oid_val(val_as_str)
    if len(data) > 1:
        return data
    return None


logger_reduce_msg_writer = logging.getLogger('reduce_log')
logger_msg_writer = logging.getLogger('msg_writer')
# noinspection PyUnusedLocal
def __callback(transportDispatcher, transportDomain, transportAddress, wholeMsg):


    while wholeMsg:
        msgVer = int(api.decodeMessageVersion(wholeMsg))
        if msgVer in api.PROTOCOL_MODULES:
            pMod = api.PROTOCOL_MODULES[msgVer]

        else:
            print("Unsupported SNMP version %s" % msgVer)
            return

        reqMsg, wholeMsg = decoder.decode(
            wholeMsg,
            asn1Spec=pMod.Message(),
        )

        print(
            "Notification message from {}:{}: ".format(
                transportDomain, transportAddress
            )
        )

        reqPDU = pMod.apiMessage.get_pdu(reqMsg)
        if reqPDU.isSameTypeWith(pMod.TrapPDU()):
            if msgVer == api.SNMP_VERSION_1:
                print(
                    "Enterprise: %s"
                    % (pMod.apiTrapPDU.get_enterprise(reqPDU).prettyPrint())
                )
                print(
                    "Agent Address: %s"
                    % (pMod.apiTrapPDU.get_agent_address(reqPDU).prettyPrint())
                )
                print(
                    "Generic Trap: %s"
                    % (pMod.apiTrapPDU.get_generic_trap(reqPDU).prettyPrint())
                )
                print(
                    "Specific Trap: %s"
                    % (pMod.apiTrapPDU.get_specific_trap(reqPDU).prettyPrint())
                )
                print(
                    "Uptime: %s" % (pMod.apiTrapPDU.get_timestamp(reqPDU).prettyPrint())
                )
                varBinds = pMod.apiTrapPDU.get_varbinds(reqPDU)

            else:
                varBinds = pMod.apiPDU.get_varbinds(reqPDU)

            # print("Var-binds:")
            vb_as_dict = get_varbinds_as_dict(varBinds)
            if vb_as_dict is not None:
                current_time_ticks =  vb_as_dict[Fields.current_time_ticks]
                # print(f'current_time_ticks: {current_time_ticks}')
                # print(f'last_time_ticks[0]: {last_time_ticks[0]}')
                vb_as_dict[Fields.time_delta] = datetime.timedelta(seconds=current_time_ticks/100) - datetime.timedelta(seconds=last_time_ticks[0]/100 if last_time_ticks[0] > 0 else last_time_ticks[0])
                last_time_ticks[0] = current_time_ticks
                # print(f'-' * 40)
                # print(f'current_time_ticks: {current_time_ticks}')
                # print(f'last_time_ticks[0]: {last_time_ticks[0]}')


                stage_val = vb_as_dict[Fields.stage_val]
                stage_num = vb_as_dict[Fields.stage_num]
                td = vb_as_dict[Fields.time_delta]

                msg = (
                    f'Stage snmp trap: num={stage_num} | val={stage_val} | '
                    f'Time ticks={vb_as_dict[Fields.current_time_ticks]} | '
                    f'Previous stage change: {td.seconds} seconds, {td.microseconds} microseconds'
                )

                logger_reduce_msg_writer.info(msg)
            print(vb_as_dict)

    return wholeMsg



transportDispatcher = AsyncioDispatcher()

transportDispatcher.register_recv_callback(__callback)

# UDP/IPv4
transportDispatcher.register_transport(
    udp.DOMAIN_NAME, udp.UdpAsyncioTransport().open_server_mode(("192.168.45.248", 164))
)

# UDP/IPv6
transportDispatcher.register_transport(
    udp6.DOMAIN_NAME, udp6.Udp6AsyncioTransport().open_server_mode(("::1", 164))
)

transportDispatcher.job_started(1)

try:
    print("This program needs to run as root/administrator to monitor port 164.")
    print("Started. Press Ctrl-C to stop")
    # Dispatcher will never finish as job#1 never reaches zero
    transportDispatcher.run_dispatcher()

except KeyboardInterrupt:
    print("Shutting down...")

finally:
    transportDispatcher.close_dispatcher()
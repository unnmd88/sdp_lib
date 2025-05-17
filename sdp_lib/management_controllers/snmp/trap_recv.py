import datetime
from collections.abc import Callable
from enum import StrEnum

from pysnmp.carrier.asyncio.dispatch import AsyncioDispatcher
from pysnmp.carrier.asyncio.dgram import udp, udp6
from pyasn1.codec.ber import decoder
from pysnmp.proto import api
import logging
from sdp_lib.management_controllers.snmp import oids
from sdp_lib.management_controllers.snmp import snmp_utils
from sdp_lib.utils_common

from sdp_lib import logging_config


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

def callback(tr_dispatcher, transport_domain, transport_address, whole_msg):

    while whole_msg:
        msg_ver = int(api.decodeMessageVersion(whole_msg))
        if msg_ver in api.PROTOCOL_MODULES:
            p_mod = api.PROTOCOL_MODULES[msg_ver]
        else:
            print(f'Unsupported SNMP version {msg_ver}')
            return

        req_msg, whole_msg = decoder.decode(
            whole_msg,
            asn1Spec=p_mod.Message(),
        )

        print(
            "Notification message from {}:{}: ".format(
                transport_domain, transport_address
            )
        )

        req_pdu = p_mod.apiMessage.get_pdu(req_msg)
        if req_pdu.isSameTypeWith(p_mod.TrapPDU()):

            varBinds = p_mod.apiPDU.get_varbinds(req_pdu)
            vb_as_dict = get_varbinds_as_dict(varBinds)
            if vb_as_dict is not None:
                current_time_ticks =  vb_as_dict[Fields.current_time_ticks]

                vb_as_dict[Fields.time_delta] = datetime.timedelta(seconds=current_time_ticks/100) - datetime.timedelta(seconds=last_time_ticks[0]/100 if last_time_ticks[0] > 0 else last_time_ticks[0])
                last_time_ticks[0] = current_time_ticks

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

    return whole_msg

def setup_dispatcher(
    ip_addr_dest: str,
    port_destination: int,
    callback_fn: Callable
) -> AsyncioDispatcher:

    tr_dispatcher = AsyncioDispatcher()
    tr_dispatcher.register_recv_callback(callback_fn)

    # UDP/IPv4
    tr_dispatcher.register_transport(
        udp.DOMAIN_NAME, udp.UdpAsyncioTransport().open_server_mode((ip_addr_dest, port_destination))
    )

    return tr_dispatcher


class TrapServer:
    def __init__(self, ip_v4, port):
        self.ip_v4 = ip_v4
        self.port = port

    def __setattr__(self, key, value):
        if key == 'ip_v4':






ip_addr_destination = '192.168.45.248'
port = 164
transport_dispatcher = setup_dispatcher(ip_addr_destination, port, callback)

try:
    print("Started. Press Ctrl-C to stop")
    # Dispatcher will never finish as job#1 never reaches zero
    transport_dispatcher.job_started(1)
    transport_dispatcher.run_dispatcher()
except KeyboardInterrupt:
    print("Shutting down...")

finally:
    transport_dispatcher.close_dispatcher()
import logging
import time

from dotenv import load_dotenv

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.snmp.snmp_utils import parse_varbinds_to_dict
from sdp_lib.management_controllers.snmp.trap_server.server import TrapReceiver
from sdp_lib.management_controllers.snmp.trap_server.handlers import CycleAndStagesHandler, HandlersManagement
from sdp_lib.management_controllers.structures import TrapTransport

load_dotenv()

all_trap_logger = logging.getLogger('trap_common')


handlers = HandlersManagement()
stages_data = {
    1: (7, 7),
    4: (1, 8),
    5: (4, 6),
    7: (5, 8),
}
handlers.register_handlers(
    ('10.45.154.11', CycleAndStagesHandler(AllowedControllers.POTOK_S, '10.45.154.11', stages_data))
)


def _cbFun(snmp_engine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
    # Callback function for receiving notifications
    # noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
    exec_context = snmp_engine.observer.get_execution_context('rfc3412.receiveMessage:request')
    source = exec_context["transportAddress"][TrapTransport.ip_address]
    domain = exec_context["transportDomain"]

    print(f'Notification from {source}, Domain {domain}')
    parsed_varbinds = parse_varbinds_to_dict(varbinds=varBinds)

    varbinds_as_str = " | ".join(f'{oid}={val}' for oid, val in parsed_varbinds.items())
    all_trap_logger.info( f'Source: {source}\nVarbinds: {varbinds_as_str}')

    curr_source_handlers = handlers.get_handlers(source)
    for handler in curr_source_handlers:
        handler(parsed_varbinds, int(time.time()))


server = TrapReceiver(
        net_interfaces=[('192.168.45.248', 164)],
        community_data=[ ("public", "public"), ("UTMC", "UTMC"),],
        cb_func=_cbFun
    )

try:
    server.run()
except KeyboardInterrupt:
    print(f'Ctrl-C was pressed.')
finally:
    server.shutdown()



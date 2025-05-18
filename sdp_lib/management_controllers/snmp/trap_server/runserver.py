from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.snmp.snmp_utils import parse_varbinds_to_dict
from sdp_lib.management_controllers.snmp.trap_server.server import TrapReceiver
from sdp_lib.management_controllers.snmp.trap_server.handlers import StageEvents, HandlersData
from sdp_lib.management_controllers.structures import TrapTransport


handlers = HandlersData()
handlers.register_handlers(('10.45.154.11', StageEvents(AllowedControllers.POTOK_S)))


def _cbFun(snmp_engine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
    # Callback function for receiving notifications
    # noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
    exec_context = snmp_engine.observer.get_execution_context('rfc3412.receiveMessage:request')
    source = exec_context["transportAddress"]
    domain = exec_context["transportDomain"]
    print(f'Notification from {source}, Domain {domain}')
    parsed_varbinds = parse_varbinds_to_dict(varbinds=varBinds)

    curr_source_handlers = handlers.get_handlers(source[TrapTransport.ip_address])
    for handler in curr_source_handlers:
        handler(parsed_varbinds)


server = TrapReceiver(
        net_interfaces=[('192.168.45.248', 164)],
        community_data=[("my-area", "public")],
        cb_func=_cbFun
    )

try:
    server.run()
except KeyboardInterrupt:
    print(f'Ctrl-C was pressed.')
finally:
    server.shutdown()




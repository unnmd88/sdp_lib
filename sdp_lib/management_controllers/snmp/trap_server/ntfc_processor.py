import collections
import pickle
import time
import logging

from sdp_lib.management_controllers.snmp.snmp_utils import parse_varbinds_to_dict
from sdp_lib.management_controllers.snmp.trap_server.handlers import HandlersManagement
from sdp_lib.management_controllers.structures import TrapTransport
from sdp_lib import logging_config


all_trap_logger = logging.getLogger('trap_common')
verbose_trap_logger = logging.getLogger('trap_verbose')


handlers = HandlersManagement()


def callback_func(snmp_engine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
    # Callback function for receiving notifications
    # noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
    exec_context = snmp_engine.observer.get_execution_context('rfc3412.receiveMessage:request')
    source = exec_context["transportAddress"][TrapTransport.ip_address]
    domain = exec_context["transportDomain"]

    if handlers.stdout_notifications:
        print(f'Notification from {source}, Domain {domain}')
    parsed_varbinds = parse_varbinds_to_dict(varbinds=varBinds)

    if handlers.logging_all_incoming_notifications:
        varbinds_as_str = " | ".join(f'{oid}={val}' for oid, val in parsed_varbinds.items())
        all_trap_logger.info( f'Source: {source}\nVarbinds: {varbinds_as_str}')

    curr_source_handlers = handlers.get_handlers(source)
    for handler in curr_source_handlers:
        handler(parsed_varbinds, int(time.time()))


if __name__ == '__main__':

    with open('vb.pkl' , 'rb') as f:
        obj = pickle.load(f)
        print(obj)
    vb = parse_varbinds_to_dict(obj)

    print(vb)

    c = collections.deque('12345')

    print(c)
    print(c[0])
    print(c[-1])
    print('------')

    while c:
        print(c.pop())
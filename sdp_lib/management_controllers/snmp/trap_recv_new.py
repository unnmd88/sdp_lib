import collections
import sys
from collections.abc import Sequence, Callable
from enum import StrEnum
from functools import cached_property
from typing import TypeAlias, Any

from pysnmp.entity import engine, config
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity.engine import SnmpEngine
from pysnmp.entity.rfc3413 import ntfrcv
import ipaddress


from sdp_lib.utils_common.utils_common import check_is_ipv4


T_Interfaces: TypeAlias = Sequence[tuple[str, int]]
T_CommunityData: TypeAlias = Sequence[tuple[str, str]]


def handler1(varbinds, *args, **kwargs):
    print(f'< Handler 1 >')
    for name, val in varbinds:
        print(f"{str(name)} = {str(val)}")
    print(f'End handler 1')


def handler2(varbinds, *args, **kwargs):
    print(f'< Handler 2 >')
    for name, val in varbinds:
        print(f"{str(name)} = {str(val)}")
    print(f'End handler 2')


class HandlersData:
    def __init__(self):
        self._handlers = {}
        self._max_handlers = 10

    def register_handlers(self, *args: tuple[str, Callable]):
        for ip, handler in args:
            if not callable(handler):
                raise ValueError(f'Обработчик должен быть вызываемым объектом')
            ipaddress.IPv4Address(ip)
            if ip not in self._handlers:
                self._handlers[ip] = collections.deque(maxlen=self._max_handlers)
            self._handlers[ip].append(handler)

    def get_registered_handlers(self):
        return self._handlers


handlers = HandlersData()
handlers.register_handlers(('10.45.154.11', handler1), ('10.45.154.11', handler2),
                           ('10.45.154.12', handler1))


def _cbFun(snmp_engine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
    # Callback function for receiving notifications
    # noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
    exec_context = snmp_engine.observer.get_execution_context('rfc3412.receiveMessage:request')
    source = exec_context["transportAddress"]
    domain = exec_context["transportDomain"]
    print(f'Notification from {source}, Domain {domain}')
    for ip, handler in handlers.get_registered_handlers().items():
        print(f'ip: {ip}\nhandler: {handler.__name__}')
    # for name, val in varBinds:
    #     # print(f"{name.prettyPrint()} = {val.prettyPrint()}")
    #     print(f"{str(name)} = {str(val)}")


class TrapReceiver:
    def __init__(
            self,
            *,
            net_interfaces: T_Interfaces,
            community_data: T_CommunityData,
    ):
        self._snmp_engine = engine.SnmpEngine()
        self._net_interfaces = net_interfaces
        self._community_data = community_data

    def _add_transport_target(self):
        for i, interface in enumerate(self._net_interfaces, 1):
            ip_v4, port = interface
            if not check_is_ipv4(ip_v4):
                raise ValueError(f'Некорректно задан ip адрес: {ip_v4}')
            elif not 0 < int(port) < 65535:
                raise ValueError(f'Некорректно задан порт: {port}')
            # UDP over IPv4, second listening interface/port
            config.add_transport(
                self._snmp_engine,
                udp.DOMAIN_NAME + (i,),
                udp.UdpTransport().open_server_mode((ip_v4, port)),
            )

    def _register_community(self):
        for community_index, community_name in self._community_data:
            # SecurityName <-> CommunityName mapping
            config.add_v1_system(self._snmp_engine, community_index, community_name)

    def _register_receiver(self):
        # Register SNMP Application at the SNMP engine
        ntfrcv.NotificationReceiver(self._snmp_engine, _cbFun)

    def _setup(self):
        self._add_transport_target()
        self._register_community()
        self._register_receiver()

    def run(self):
        self._setup()
        self._snmp_engine.transport_dispatcher.job_started(1)
        self._snmp_engine.open_dispatcher()
        print("Started. Press Ctrl-C to stop")

    def shutdown(self):
        print("Shutting down...")
        self._snmp_engine.close_dispatcher()


if __name__ == '__main__':
    server = TrapReceiver(
        net_interfaces=[('192.168.45.248', 164)],
        community_data=[("my-area", "public")]
    )
    try:
        server.run()
    except KeyboardInterrupt:
        print(f'Ctrl-C was pressed.')
    finally:
        server.shutdown()

    # print(handlers.get_registered_handlers())
from collections.abc import Sequence, Callable
from enum import StrEnum
from runpy import run_path
from typing import TypeAlias

from pysnmp.entity import engine, config
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity.engine import SnmpEngine
from pysnmp.entity.rfc3413 import ntfrcv
import ipaddress

from sdp_lib.utils_common.utils_common import check_is_ipv4

# Create SNMP engine with autogenernated engineID and pre-bound
# to socket transport dispatcher
snmp_engine = engine.SnmpEngine()

# Transport setup

# UDP over IPv4, first listening interface/port
# config.add_transport(
#     snmp_engine,
#     udp.DOMAIN_NAME + (1,),
#     udp.UdpTransport().open_server_mode(("192.168.45.248", 164)),
# )

# UDP over IPv4, second listening interface/port
# config.add_transport(
#     snmpEngine,
#     udp.DOMAIN_NAME + (2,),
#     udp.UdpTransport().open_server_mode(("127.0.0.1", 2162)),
# )

T_Interfaces: TypeAlias = Sequence[tuple[str, int]]
T_CommunityData: TypeAlias = Sequence[tuple[str, str]]

def _cbFun(snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
    # Callback function for receiving notifications
    # noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
    # print(
    #     'Notification from ContextEngineId "{}", ContextName "{}"'.format(
    #         contextEngineId.prettyPrint(), contextName.prettyPrint()
    #     )
    # )
    exec_context = snmpEngine.observer.get_execution_context(
        'rfc3412.receiveMessage:request'
    )
    print(
        f'Notification from {exec_context["transportAddress"]}, Domain {exec_context["transportDomain"]}'
    )


    # print(f'snmpEngine: {type(snmpEngine)}\n')
    # print(f'snmpEngine cache: {snmpEngine.cache}\n'
    #       f'execContext c: {execContext}\n',
    #       f'stateReference: {type(stateReference)}\n'
    #       f'contextEngineId: {type(contextEngineId)}\n'
    #       f'contextName: {type(contextName)}\n'
    #       f'cbCtx: {type(cbCtx)}')

    for name, val in varBinds:
        # print(f"{name.prettyPrint()} = {val.prettyPrint()}")
        print(f"{str(name)} = {str(val)}")

def add_transport(
    snmp_engine: SnmpEngine,
    net_interfaces: T_Interfaces
):
    for i, interface in enumerate(net_interfaces, 1):
        ip_v4, port = interface
        if not check_is_ipv4(ip_v4):
            raise ValueError(f'Некорректно задан ip адрес: {ip_v4}')
        elif not 0 < int(port) < 65535:
            raise ValueError(f'Некорректно задан порт: {port}')
        # UDP over IPv4, second listening interface/port
        config.add_transport(
            snmp_engine,
            udp.DOMAIN_NAME + (i,),
            udp.UdpTransport().open_server_mode((ip_v4, port)),
        )

def register_community(
    snmp_engine: SnmpEngine,
    community_data: T_CommunityData
):
    for community_index, community_name in community_data:
        # SecurityName <-> CommunityName mapping
        config.add_v1_system(snmp_engine, community_index, community_name)

def register_receiver(
    snmp_engine: SnmpEngine,
    callback_func: Callable
):
    # Register SNMP Application at the SNMP engine
    ntfrcv.NotificationReceiver(snmp_engine, _cbFun)

def setup_receiver(
    snmp_engine: SnmpEngine,
    interfaces: T_Interfaces,
    community_data: T_CommunityData,
    callback_func: Callable
):
    add_transport(snmp_engine, interfaces)
    register_community(snmp_engine, community_data)
    register_receiver(snmp_engine, callback_func)


class Handlers(StrEnum):
    stage = 'stage'


class TrapReceiver:
    def __init__(
            self,
            *,
            net_interfaces: T_Interfaces,
            community_data: T_CommunityData,
            handlers: Sequence[Callable] = None
    ):
        self._snmp_engine = engine.SnmpEngine()
        self._net_interfaces = net_interfaces
        self._community_data = community_data
        self._handlers = handlers


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

    def _register_handlers(self):
        if self._handlers is not None:
            for handler in self._handlers:
                try:
                    Handlers(handler)
                except ValueError:
                    print(f'Обработчик должен быть из {Handlers}')

    def _setup(self):
        self._add_transport_target()
        self._register_community()
        self._register_receiver()
        self._register_handlers()

    def run(self):
        self._setup()
        self._snmp_engine.transport_dispatcher.job_started(1)
        self._snmp_engine.open_dispatcher()
        print("Started. Press Ctrl-C to stop")

    def shutdown(self):
        print("Shutting down...")
        self._snmp_engine.close_dispatcher()


# SNMPv1/2c setup

# SecurityName <-> CommunityName mapping
# config.add_v1_system(snmp_engine, "my-area", "public")


if __name__ == '__main__':
    try:
        # Create SNMP engine with autogenernated engineID and pre-bound
        # to socket transport dispatcher
        server = TrapReceiver(
            net_interfaces=[('192.168.45.248', 164)],
            community_data=[("my-area", "public")]
        )
        server.run()
        # snmp_engine = engine.SnmpEngine()
        # setup_receiver()
        # snmp_engine.transport_dispatcher.job_started(1)  # this job would never finish
        # Run I/O dispatcher which would receive queries and send confirmations
        # snmp_engine.open_dispatcher()
    except KeyboardInterrupt:
        print(f'Ctrl-C was pressed.')
    finally:
        server.shutdown()
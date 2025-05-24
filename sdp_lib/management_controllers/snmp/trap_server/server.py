import pprint
import tomllib
from collections.abc import (
    Sequence,
    Callable, MutableMapping
)
from typing import TypeAlias, Any

from pysnmp.entity import (
    engine,
    config
)
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

from sdp_lib.utils_common.utils_common import check_is_ipv4


T_Interfaces: TypeAlias = Sequence[tuple[str, int]]
T_CommunityData: TypeAlias = Sequence[tuple[str, str]]


class TrapReceiver:
    def __init__(
            self,
            *,
            net_interfaces: T_Interfaces,
            community_data: T_CommunityData,
            cb_func: Callable
    ):
        self._snmp_engine = engine.SnmpEngine()
        self._net_interfaces = net_interfaces
        self._community_data = community_data
        self._cb_func = cb_func

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
        ntfrcv.NotificationReceiver(self._snmp_engine, self._cb_func)

    def _setup(self):
        self._add_transport_target()
        self._register_community()
        self._register_receiver()

    def run(self):
        self._setup()
        self._snmp_engine.transport_dispatcher.job_started(1)
        print("Started. Press Ctrl-C to stop")
        self._snmp_engine.open_dispatcher()


    def shutdown(self):
        print("Shutting down...")
        self._snmp_engine.close_dispatcher()


if __name__ == '__main__':
    conf = Config()
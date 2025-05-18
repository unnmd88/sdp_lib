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

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.parsers.snmp_parsers.processing_methods import get_val_as_str
from sdp_lib.management_controllers.snmp import oids, snmp_utils
from sdp_lib.management_controllers.snmp.trap_recv import Fields
from sdp_lib.utils_common.utils_common import check_is_ipv4


T_Interfaces: TypeAlias = Sequence[tuple[str, int]]
T_CommunityData: TypeAlias = Sequence[tuple[str, str]]


class AbstractEventProcessors:
    def __init__(self, type_controller: AllowedControllers):
        self._type_controller = type_controller
        self._max_log_messages = 20
        self.time_ticks = 0
        self.time_ticks_oid = self._get_time_ticks_oid()
        self._messages_to_write = collections.deque(maxlen=self._max_log_messages)

    def __call__(self, *args, **kwargs):
        varbinds: dict[str, Any]  = args[0]
        self.time_ticks = varbinds.get(self.time_ticks_oid)
        print(f'TIME_TICKS: {self.time_ticks}')
        self.process_event(varbinds)

    def set_max_messages(self, val: int):
        self._max_log_messages = int(val)

    def process_event(self, *args, **kwargs):
        pass

    def _get_time_ticks_oid(self):
        if self._type_controller in (AllowedControllers.POTOK_S, AllowedControllers.SWARCO):
            return '1.3.6.1.2.1.1.3.0'
        else:
            raise NotImplementedError()


class StageEventProcessors(AbstractEventProcessors):
    def __init__(self, type_controller):
        super().__init__(type_controller)
        self._expected_oid = self._get_expected_oid()

    def _get_expected_oid(self):
        if self._type_controller in (AllowedControllers.POTOK_S, AllowedControllers.SWARCO):
            return oids.Oids.swarcoUTCTrafftechPhaseStatus
        else:
            raise NotImplementedError()

    @cached_property
    def stage_handlers(self):
        return {
            AllowedControllers.POTOK_S: [
                (Fields.stage_val, get_val_as_str),
                (Fields.stage_num, snmp_utils.StageConverterMixinPotokS.get_num_stage_from_oid_val),
            ]
        }

    def process_event(self, parsed_varbinds: dict[str, Any]):
        print(f'process_stage')
        print(f'parsed_varbinds: {parsed_varbinds}')
        try:
            oid_val = parsed_varbinds[self._expected_oid]
        except KeyError:
            return

        for field_name, handler in self.stage_handlers.get(self._type_controller):
            msg = (
                f'{field_name}={handler(oid_val)}'
            )
            self._messages_to_write.append(msg)

        for m in self._messages_to_write:
            with open('Tets_msg', 'a') as f:
                f.write(m + '\n')


def parse_varbinds(varbinds):
    return {str(k): v.prettyPrint() for k, v in varbinds}
    # for name, val in varbinds:
    #     print(f"{name.prettyPrint()} = {val.prettyPrint()}")


class HandlersData:
    def __init__(self):
        self._handlers = {}
        self._max_handlers = 10

    def register_handlers(self, *args: tuple[str, Callable]):
        for ip, handler in args:
            # if not callable(handler):
            #     raise ValueError(f'Обработчик должен быть вызываемым объектом')
            ipaddress.IPv4Address(ip)
            if ip not in self._handlers:
                self._handlers[ip] = collections.deque(maxlen=self._max_handlers)
            self._handlers[ip].append(handler)

    @cached_property
    def registered_handlers(self) -> dict[str, Sequence[Callable]]:
        return self._handlers

    def get_handlers(self, ip_address: str) -> Sequence[Callable]:
        return self._handlers.get(ip_address, [])


handlers = HandlersData()
# handlers.register_handlers(('10.45.154.11', handler1), ('10.45.154.11', handler2),
#                            ('10.45.154.12', handler1))
handlers.register_handlers(('10.45.154.11', StageEventProcessors(AllowedControllers.POTOK_S)))



IP_ADDRESS = 0
PORT       = 1

def _cbFun(snmp_engine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
    # Callback function for receiving notifications
    # noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
    exec_context = snmp_engine.observer.get_execution_context('rfc3412.receiveMessage:request')
    source = exec_context["transportAddress"]
    domain = exec_context["transportDomain"]
    print(f'Notification from {source}, Domain {domain}')
    parsed_varbinds = parse_varbinds(varbinds=varBinds)

    curr_source_handlers = handlers.get_handlers(source[IP_ADDRESS])
    for handler in curr_source_handlers:
        handler(parsed_varbinds)



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
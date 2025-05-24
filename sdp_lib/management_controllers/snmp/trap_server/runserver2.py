import pprint
import tomllib
import logging
import time
from collections.abc import MutableMapping, Sequence
from enum import StrEnum
from typing import NamedTuple

from dotenv import load_dotenv

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.snmp.snmp_utils import parse_varbinds_to_dict
from sdp_lib.management_controllers.snmp.trap_server.server import TrapReceiver
from sdp_lib.management_controllers.snmp.trap_server.handlers import (
    CycleAndStagesHandler,
    HandlersManagement
)
from sdp_lib.management_controllers.structures import TrapTransport

load_dotenv()

all_trap_logger = logging.getLogger('trap_common')

DEBUG = True


class Fields(StrEnum):
    handlers = 'handlers'
    cycles = 'cycles'
    network_interfaces = 'network_interfaces'


class NetworkInterfaces(NamedTuple):
    ip: str
    port: int


class CycleConfig(NamedTuple):
    ip: str
    type_controller: AllowedControllers
    start_stage: int
    prom_tacts: MutableMapping = dict()


class Config:

    err_log_filename = 'errors.log'

    def __init__(self, source):
        self._source = source
        self._config = self.get_config()

    def write_to_err_log(self, message):
        with open(self.err_log_filename, 'a') as err_log:
            err_log.write(message)

    def get_config(self) -> MutableMapping:
        parsed_config, error = {}, None
        try:
            with open(self._source, 'rb') as f:
                parsed_config = tomllib.load(f)
                pprint.pprint(parsed_config)
        except tomllib.TOMLDecodeError as e:
            error = f'\nОшибка в файле {self._source}:\n{str(e)}'
        except FileNotFoundError as e:
            error = f'\n{str(e)}'

        print('ffffff')

        try:
            parsed_config[Fields.network_interfaces] = [
                NetworkInterfaces(*net_interface) for net_interface in parsed_config[Fields.network_interfaces]
            ]
        except KeyError as e:
            error = f'\nНет зарегистрированных сетевых интерфейсов для приёма traps:\n{str(e)}'

        if error is None:
            try:
                cycles = parsed_config[Fields.handlers][Fields.cycles]
                parsed_config[Fields.handlers][Fields.cycles] = [CycleConfig(*cycle) for cycle in cycles]
            except KeyError:
                pass

        pprint.pprint(parsed_config)

        if error is not None:
            self.write_to_err_log(error)
        return parsed_config

    def convert_key_and_val_to_int(self, m_mapping: MutableMapping):
        return {int(k): float(v) for k, v in m_mapping.items()}

    def get_handlers(self):
        return self._config.get(Fields.handlers)

    @property
    def net_interfaces(self) -> Sequence[NetworkInterfaces]:
        return self._config[Fields.network_interfaces]

    @property
    def is_valid(self):
        return bool(self._config)

    @property
    def has_handlers(self):
        return bool(self._config.get(Fields.handlers))

    @property
    def cycle_handlers(self) -> list[CycleConfig]:
        try:
            return self._config[Fields.handlers][Fields.cycles]
        except KeyError:
            return []


config = Config('t.toml')

handlers = HandlersManagement()

for h in config.cycle_handlers:
    handlers.register_handlers(
        (h.ip, CycleAndStagesHandler(h.type_controller, h.ip, h.prom_tacts))
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
        net_interfaces=[*config.net_interfaces],
        community_data=[ ("public", "public"), ("UTMC", "UTMC"),],
        cb_func=_cbFun
    )


if __name__ == '__main__':
    if DEBUG:
        print(config.is_valid)
        print(config.cycle_handlers)
        print(config.net_interfaces)
    else:
        try:
            server.run()
        except KeyboardInterrupt:
            print(f'Ctrl-C was pressed.')
        finally:
            server.shutdown()



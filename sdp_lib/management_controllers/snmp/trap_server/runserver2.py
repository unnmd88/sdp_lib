import pprint
import tomllib
import logging
import time
from collections.abc import MutableMapping, Sequence, Hashable
from enum import StrEnum
from pathlib import Path
from typing import NamedTuple, Any

from dotenv import load_dotenv

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.snmp.snmp_utils import parse_varbinds_to_dict
from sdp_lib.management_controllers.snmp.gen_default_config.configparser import ConfigParser
from sdp_lib.management_controllers.snmp.gen_default_config.server import TrapReceiver
from sdp_lib.management_controllers.snmp.gen_default_config.handlers import (
    CycleAndStagesHandler,
    HandlersManagement
)
from sdp_lib.management_controllers.structures import TrapTransport
from sdp_lib.management_controllers.snmp.gen_default_config import ntfc_processor
from sdp_lib import logging_config

logger = logging.getLogger('server_ntfc')

load_dotenv()


DEBUG = False

config = ConfigParser('t.toml')

logger.info('Регистрирую обработчики циклов и фаз')
cnt_registered_cycle_handlers = ntfc_processor.handlers.register_cycles(config.cycles)
logger.info(f'Количество зарегистрированных обработчиков циклов и фаз: {cnt_registered_cycle_handlers}')


server = TrapReceiver(
        net_interfaces=[*config.net_interfaces],
        community_data=[ ("public", "public"), ("UTMC", "UTMC"),],
        cb_func=ntfc_processor.callback_func
    )


if __name__ == '__main__':
    if DEBUG:
        print(config.cycles)
        print(config.net_interfaces)
    else:
        try:
            server.run()
        except KeyboardInterrupt:
            print(f'Ctrl-C was pressed.')
        finally:
            server.shutdown()



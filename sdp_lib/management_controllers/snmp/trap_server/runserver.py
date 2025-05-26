import logging

from dotenv import load_dotenv

from sdp_lib.management_controllers.snmp.trap_server.configparser import  ConfigParser
from sdp_lib.management_controllers.snmp.trap_server.server import TrapReceiver
from sdp_lib.management_controllers.snmp.trap_server import ntfc_processor
from sdp_lib import logging_config

logger = logging.getLogger('server_ntfc')
load_dotenv()


DEBUG = True

config = ConfigParser('config.toml')
ntfc_processor.handlers.load_server_config(config)


if config.has_cycles:
    logger.info('Регистрирую обработчики циклов и фаз')
    cnt_registered_cycle_handlers = ntfc_processor.handlers.register_cycles(config.cycles)
    logger.info(f'Зарегистрированные обработчики циклов и фаз: {config.cycles}')


server = TrapReceiver(
        net_interfaces=config.net_interfaces,
        community_data=config.community,
        cb_func=ntfc_processor.callback_func
    )


if __name__ == '__main__':
    if DEBUG:
        print(config.cycles)
        print(config.net_interfaces)
    else:
        try:
            logger.info('Запускаю сервер')
            server.run()
        except KeyboardInterrupt:
            print(f'Ctrl-C was pressed.')
        finally:
            server.shutdown()



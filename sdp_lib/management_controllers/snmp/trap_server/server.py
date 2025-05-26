import logging
from collections.abc import (
    Sequence,
    Callable
)
from typing import TypeAlias

from pysnmp.entity import (
    engine,
    config
)
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

from sdp_lib.utils_common.utils_common import check_is_ipv4


logger = logging.getLogger('server_ntfc')

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
                err_msg = f'Некорректно задан ip адрес: {ip_v4}'
                logger.critical(err_msg)
                raise ValueError(err_msg)
            elif not 0 < int(port) < 65535:
                err_msg = f'Некорректно задан порт: {port}'
                logger.critical(err_msg)
                raise ValueError(err_msg)
            # UDP over IPv4, second listening interface/port
            config.add_transport(
                self._snmp_engine,
                udp.DOMAIN_NAME + (i,),
                udp.UdpTransport().open_server_mode((ip_v4, port)),
            )
            logger.info(f'Сетевой интерфейс для приёма trap уведомлений зарегистрирован: {(ip_v4, port)}')

    def _register_community(self):
        for community_index, community_name in self._community_data:
            # SecurityName <-> CommunityName mapping
            config.add_v1_system(self._snmp_engine, community_index, community_name)
            logger.info(f'Успешно зарегистрировано: {(community_index, community_name)}')

    def _register_receiver_and_callback(self):
        # Register SNMP Application at the SNMP engine
        ntfrcv.NotificationReceiver(self._snmp_engine, self._cb_func)
        logger.info(f'Trap сервер успешно зарегистрирован.')
        logger.info(f'Зарегистрирована коллбэк-функция обработки trap-уведомлений: {self._cb_func.__name__}')

    def _setup(self):
        logger.info(f'Начинаю подготовку конфигурации сервера...')
        logger.info(f'Регистрирую сетевые интерфейсы приёма trap уведомлений...')
        self._add_transport_target()
        logger.info(f'Регистрирую community...')
        self._register_community()
        logger.info(f'Регистрирую сервер и коллбэк функцию для trap сообщения...')
        self._register_receiver_and_callback()

    def run(self):
        self._setup()
        self._snmp_engine.transport_dispatcher.job_started(1)
        logger.info(f'Сервер запущен. Для остановки нажмите Ctrl-C')
        print("Started. Press Ctrl-C to stop")
        self._snmp_engine.open_dispatcher()


    def shutdown(self):
        logger.info(f'Сервер остановлен.')
        print("Shutting down...")
        self._snmp_engine.close_dispatcher()


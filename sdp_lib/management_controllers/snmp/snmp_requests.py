import ipaddress
from typing import KeysView, Any, TypeVar, NamedTuple

from pysnmp.hlapi.v3arch.asyncio import *
from pysnmp.proto import errind, rfc1905

from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.snmp_utils import  HostSnmpConfig

snmp_engine = SnmpEngine()


async def get(
        ip_v4: str,
        community: str,
        oids: list[str | Oids] | tuple[str | Oids, ...] | KeysView[str | Oids],
        engine: SnmpEngine = SnmpEngine(),
        timeout: float = 0.2,
        retries: int = 0
) -> tuple:
    """
    Метод get запросов по snmp
    :param ip_v4:
    :param community: коммьюнити хоста
    :param oids: список oids, которые будут отправлены в get запросе
    :param timeout: таймаут запроса, в секундах
    :param retries: количество попыток запроса
    :return: tuple вида:
             index[0] -> если есть ошибка в snmp запросе, то текст ошибки, иначе None
             index[1] -> ответные данные. список вида [(oid, payload), (oid, payload)...]
             index[2] -> self, ссылка на объект

    Examples
    --------
    ip_adress = '192.168.0.1'\n
    community = 'community'\n
    oids = [Oids.swarcoUTCTrafftechPhaseStatus,
           Oids.swarcoUTCTrafftechPlanStatus]


    asyncio.run(set_request(ip_adress, community, oids))
    ******************************
    """
    # response = tuple(error_indication, error_status, error_index, var_binds)
    return await get_cmd(
        engine,
        CommunityData(community),
        await UdpTransportTarget.create((ip_v4, 161), timeout=timeout, retries=retries),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid), rfc1905.unSpecified) for oid in oids]
    )


async def snmp_get_next(
        ip_v4: str,
        community: str,
        oids: list[str | Oids] | KeysView[str | Oids],
        engine: SnmpEngine = SnmpEngine(),
        timeout: float = 0.2,
        retries: int = 0
):
    return await next_cmd(
        engine,
        CommunityData(community),
        await UdpTransportTarget.create((ip_v4, 161), timeout=timeout, retries=retries),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid)) for oid in oids]
    )


async def snmp_set(
        self,
        oids: list[tuple[str | Oids, Any]],
        engine: SnmpEngine = SnmpEngine(),
        timeout: float = 1,
        retries: int = 0
):
    error_indication, error_status, error_index, var_binds = await set_cmd(
        SnmpEngine() or engine,
        CommunityData(self.community_w),
        await UdpTransportTarget.create((self._ipv4, 161), timeout=timeout, retries=retries),
        ContextData(),
        *[ObjectType(ObjectIdentity(oid), val) for oid, val in oids]
        # *[ObjectType(ObjectIdentity('1.3.6.1.4.1.1618.3.7.2.11.1.0'), Unsigned32('2')) for oid, val in oids]
    )
    print(error_indication, error_status, error_index, var_binds)
    return error_indication, error_status, error_index, var_binds


class AsyncSnmpRequests:

    def __init__(self, engine: SnmpEngine, config: HostSnmpConfig, ipv4: str = ''):
        self._ipv4 = ipv4
        self._engine = engine
        self._config = config

    @property
    def ipv4(self):
        return self.ipv4

    def set_ipv4(self, ipv4: str):
        self._ipv4 = str(ipaddress.IPv4Address(ipv4))

    def set_timeout(self, val: float):
        self._timeout = float(val)

    def set_retries(self, val: int):
        self._retries = int(val)

    async def snmp_get(
            self,
            varbinds: list[ObjectType] | tuple[ObjectType],
            timeout: float = 1,
            retries: int = 0
    ) -> tuple[errind.ErrorIndication, Integer32 | int, Integer32 | int, tuple[ObjectType, ...]]:
        """
        Метод get запросов по snmp v2 протоколу.
        :param oids: список oids, которые будут отправлены в get запросе.
        :param timeout: таймаут запроса, в секундах.
        :param retries: количество попыток запроса.
        :return: tuple вида (error_indication, error_status, error_index, var_binds)
                 error_indication -> errind.ErrorIndication, если есть ошибка в запросе/ответе,
                                    иначе None.
                 error_status -> Статус ошибки, числовое представление
                 error_index -> Индекс ошибки, числовое представление
                 var_binds -> кортеж с ответами оидов, где str(var_binds[0]) - это оид,
                              а str(var_binds[1]) - значение оида.

        Examples
        --------
        ip_adress = '192.168.0.1'\n
        community = 'community'\n
        oids = [Oids.swarcoUTCTrafftechPhaseStatus,
               Oids.swarcoUTCTrafftechPlanStatus]

        response: (error_indication, error_status, error_index, var_binds)
        asyncio.run(set_request(ip_adress, community, oids))
        ******************************
        """
        # print(f'oids: {oids}')
        return await get_cmd(
            self._engine,
            CommunityData(self._config.community_r),
            await UdpTransportTarget.create((self._ipv4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *varbinds
        )
        # print(f'error_indication: {error_indication}\n'
        #       f'error_status: {error_status}\n'
        #       f'error_index: {error_index}\n'
        #       f'var_binds: {var_binds}')

        # return self.check_response_and_add_error_if_has(error_indication, error_status, error_index), var_binds

    async def snmp_set(
            self,
            varbinds: tuple[ObjectType, ...] | list[ObjectType],
            timeout: float = 1,
            retries: int = 0
    ) -> tuple[errind.ErrorIndication, Integer32 | int, Integer32 | int, tuple[ObjectType, ...]]:

        return await set_cmd(
            self._instance_host.driver or snmp_engine,
            CommunityData(self.community_w),
            await UdpTransportTarget.create((self.ip, 161), timeout= timeout, retries=retries),
            ContextData(),
            *varbinds
            # *[ObjectType(ObjectIdentity(oid), val) for oid, val in oids]
            # *[ObjectType(ObjectIdentity('1.3.6.1.4.1.1618.3.7.2.11.1.0'), Unsigned32('2')) for oid, val in oids]
        )

    async def snmp_get_next(
            self,
            varbinds: list[ObjectType] | tuple[ObjectType],
            timeout: float = 1,
            retries: int = 0
    ) -> tuple[errind.ErrorIndication, Integer32 | int, Integer32 | int, tuple[ObjectType, ...]]:
        """
        Метод get запросов по snmp v2 протоколу.
        :param oids: список oids, которые будут отправлены в get запросе.
        :param timeout: таймаут запроса, в секундах.
        :param retries: количество попыток запроса.
        :return: tuple вида (error_indication, error_status, error_index, var_binds)
                 error_indication -> errind.ErrorIndication, если есть ошибка в запросе/ответе,
                                    иначе None.
                 error_status -> Статус ошибки, числовое представление
                 error_index -> Индекс ошибки, числовое представление
                 var_binds -> кортеж с ответами оидов, где str(var_binds[0]) - это оид,
                              а str(var_binds[1]) - значение оида.

        Examples
        --------
        ip_adress = '192.168.0.1'\n
        community = 'community'\n
        oids = [Oids.swarcoUTCTrafftechPhaseStatus,
               Oids.swarcoUTCTrafftechPlanStatus]

        response: (error_indication, error_status, error_index, var_binds)
        asyncio.run(set_request(ip_adress, community, oids))
        ******************************
        """
        # print(f'oids: {oids}')
        return await next_cmd(
            self._instance_host.driver or snmp_engine,
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip, 161), timeout=timeout, retries=retries),
            ContextData(),
            *varbinds
        )
        # print(f'error_indication: {error_indication}\n'
        #       f'error_status: {error_status}\n'
        #       f'error_index: {error_index}\n'
        #       f'var_binds: {var_binds}')

        # return self.check_response_and_add_error_if_has(error_indication, error_status, error_index), var_binds


class AsyncSnmpRequestsCustom:
    def __init__(
            self, 
            *, ip: str, 
            community_read: str, 
            community_write: str | None, 
            timeout: float, retries: int, 
            engine: SnmpEngine = snmp_engine
    ):
        self._ip = ip
        self._community_read = community_read
        self._community_write = community_write
        self._timeout: float = timeout or 0.6
        self._retries = retries or 1
        self._engine = engine

    async def get_by_varbinds(
            self,
            varbinds: list[ObjectType] | tuple[ObjectType],

    ) -> tuple[errind.ErrorIndication, Integer32 | int, Integer32 | int, tuple[ObjectType, ...]]:
        """
        Метод get запросов по snmp v2 протоколу.
        :param oids: список oids, которые будут отправлены в get запросе.
        :param timeout: таймаут запроса, в секундах.
        :param retries: количество попыток запроса.
        :return: tuple вида (error_indication, error_status, error_index, var_binds)
                 error_indication -> errind.ErrorIndication, если есть ошибка в запросе/ответе,
                                    иначе None.
                 error_status -> Статус ошибки, числовое представление
                 error_index -> Индекс ошибки, числовое представление
                 var_binds -> кортеж с ответами оидов, где str(var_binds[0]) - это оид,
                              а str(var_binds[1]) - значение оида.

        Examples
        --------
        ip_adress = '192.168.0.1'\n
        community = 'community'\n
        oids = [Oids.swarcoUTCTrafftechPhaseStatus,
               Oids.swarcoUTCTrafftechPlanStatus]

        response: (error_indication, error_status, error_index, var_binds)
        asyncio.run(set_request(ip_adress, community, oids))
        ******************************
        """

        return await get_cmd(
            self._engine,
            CommunityData(self._community_read),
            await UdpTransportTarget.create((self._ip, 161), timeout=self._timeout, retries=self._retries),
            ContextData(),
            *varbinds
        )

    def set_timeout(self, val: float):
        self._timeout = val

    def set_retries(self, val: int):
        self._retries = val
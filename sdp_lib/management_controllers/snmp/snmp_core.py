import abc
import asyncio
import functools
import json
import time
from functools import cached_property
from typing import Self, TypeVar, Any, Type
from collections.abc import Callable

from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts_core import Host, ResponseEntity
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.processing_methods import (
    get_val_as_str,
    pretty_print,
    build_func_with_remove_scn
)
from sdp_lib.management_controllers.parsers.snmp_parsers.varbinds_parsers import (
    pretty_processing_stcip_config,
    default_processing,
    BaseSnmpParser,
    ConfigsParser,
    ParsersVarbindsSwarco,
    ParsersVarbindsPotokS,
    ParsersVarbindsPotokP,
    ParsersVarbindsPeek, default_processing_ug405_config, default_processing_stcip, pretty_processing_stcip_without_extras
)
from sdp_lib.management_controllers.snmp import (
    snmp_config,
    oids, snmp_utils
)
from sdp_lib.management_controllers.structures import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.set_commands import SnmpEntity
from sdp_lib.management_controllers.snmp.snmp_utils import ScnConverterMixin, HostSnmpConfig
from sdp_lib.management_controllers.snmp.snmp_requests import AsyncSnmpRequests, snmp_engine
from sdp_lib.management_controllers.snmp import snmp_requests
from sdp_lib.management_controllers.snmp.snmp_utils import (
    swarco_stcip_varbinds,
    potok_stcip_varbinds,
    potok_ug405_varbinds,
    peek_ug405_varbinds, CommonVarbindsUg405
)
from sdp_lib.management_controllers.snmp.user_types import T_Varbinds


T_DataHosts = TypeVar('T_DataHosts', bound=HostSnmpConfig)


def ug405_dependency(
        type_request_entity: SnmpEntity,
        varbinds_builder_method: Callable
):
    def wrapper(func: Callable):
        @functools.wraps(func)
        async def wrapped(instance, value=None, *args, **kwargs):
            # print(f'dependency_varbinds: {dependency_varbinds}')
            await instance._get_dependency_data_and_add_error_if_has()
            if instance.response_errors:
                return instance

            if isinstance(instance, PeekUg405) and type_request_entity == SnmpEntity.snmp_set:
                 if instance.current_opeartion_mode == 1: # TO DO in Peek get_dependency_data_and_add_error_if_has()
                    await instance.set_operation_mode2()
                    if instance.response_errors:
                        return instance

            if value is None:
                instance._set_varbinds_for_request(varbinds_builder_method(instance.scn_as_ascii_string))
            else:
                instance._set_varbinds_for_request(varbinds_builder_method(instance.scn_as_ascii_string, value))

            # print(f'varbinds_for_req: {instance._varbinds_for_request}')
            #
            # print(f'param: {instance.host_properties.type_controller}')
            # print(f'value: {value}')
            # print(f'func_name: {func.__name__}')
            # print(f'args: {args}, kwargs: {kwargs}')
            # print(f'instanse: {instance}')
            if type_request_entity == SnmpEntity.snmp_set:
                return await func(instance, value)
            return await func(instance)

        return wrapped
    return wrapper


class SnmpHost(Host):
    """
    Класс абстрактного хоста, в котором реализована логика формирования snmp-запросов,
    получение и обработка snmp-ответов.
    """

    _parser_class: Type[ParsersVarbindsSwarco | ParsersVarbindsPotokS | ParsersVarbindsPotokP | ParsersVarbindsPeek]
    varbinds: Any
    protocol = FieldsNames.protocol_snmp

    def __init__(
            self,
            *,
            ipv4: str = None,
            host_id: str = None,
            engine: SnmpEngine = None
    ):
        super().__init__(ipv4=ipv4, host_id=host_id)
        self.set_driver(engine)
        self._request_sender = AsyncSnmpRequests(self._driver, self.snmp_config, ipv4=self._ipv4)
        self._request_varbinds: T_Varbinds | None = None
        self._snmp_method: Callable | None = None
        self._parser = self._parser_class()
        self._parser_config: ConfigsParser = default_processing

    @cached_property
    @abc.abstractmethod
    def snmp_config(self) -> HostSnmpConfig:
        """ Возвращает конфигурацию snmp протокола контроллера (ug405 | stcip | ...) """

    @classmethod
    def _get_parser(cls):
        return cls._parser_class

    @property
    def request_sender(self) -> AsyncSnmpRequests:
        return self._request_sender

    def _check_response_errors_and_add_to_response_entity_if_has(self) -> bool:
        """
            self.__response[ResponseStructure.ERROR_INDICATION] = error_indication: errind.ErrorIndication,
            self.__response[ResponseStructure.ERROR_STATUS] = error_status: Integer32 | int,
            self.__response[ResponseStructure.ERROR_INDEX] = error_index: Integer32 | int
        """
        if self._tmp_response[SnmpResponseStructure.ERROR_INDICATION]:
            self._response_storage.add_errors(self._tmp_response[SnmpResponseStructure.ERROR_INDICATION])
        elif (
            self._tmp_response[SnmpResponseStructure.ERROR_STATUS]
            or self._tmp_response[SnmpResponseStructure.ERROR_INDEX]
        ):
            self._response_storage.add_errors(BadControllerType())
        return bool(self._response_storage.errors)

    async def _make_request_and_load_response(self, create_response_entity: bool = True) -> Self:
        """
        Осуществляет вызов соответствующего snmp-запроса и передает
        self.__parse_response_all_types_requests полученный ответ для парса response.
        """
        self._tmp_response = await self._snmp_method(varbinds=self._request_varbinds)
        self._check_response_errors_and_add_to_response_entity_if_has()
        if create_response_entity:
            self._parser.load_config_parser(self._parser_config)
            self._response_storage.raw_responses.append(
                ResponseEntity(
                    raw_data=self._tmp_response[SnmpResponseStructure.VAR_BINDS],
                    name=FieldsNames.snmp_varbinds,
                    parse_method=self._parser
                )
            )
        for d in self._response_storage.raw_responses:
            print(d.parse_method(d.raw_data))

        return self


class TempSwarco(SnmpHost):

    _parser_class = ParsersVarbindsSwarco

    @cached_property
    def snmp_config(self) -> HostSnmpConfig:
        return snmp_utils.stcip_config

    async def get_states_request(self):
        self._snmp_method = self._request_sender.snmp_get
        self._request_varbinds = snmp_utils.swarco_stcip_varbinds.states_varbinds
        self._parser_config = pretty_processing_stcip_config
        await self._make_request_and_load_response()
        print(self._response_storage.raw_responses)
        print(json.dumps(snmp_utils.parse_varbinds_to_dict(self._tmp_response[SnmpResponseStructure.VAR_BINDS]), indent=4))


# class SnmpHosts(Host):
#     """
#     Класс абстрактного хоста, в котором реализована логика формирования snmp-запросов,
#     получение и обработка snmp-ответов.
#     """
#
#     parser_class: Any
#     varbinds: Any
#
#     def __init__(
#             self,
#             *,
#             ipv4: str = None,
#             host_id: str = None,
#             engine: SnmpEngine = None
#     ):
#         super().__init__(ipv4=ipv4, host_id=host_id)
#         self.set_driver(engine)
#         self._request_sender = AsyncSnmpRequests(self)
#         self._request_method: Callable | None = None
#         self._parse_method_config = None
#         self._parser: BaseSnmpParser = self._get_parser()
#
#
#     # def set_driver(self, engine: SnmpEngine):
#     #     if isinstance(engine, SnmpEngine):
#     #         self._engine = engine
#     #     else:
#     #         raise TypeError(f'engine должен быть типа "SnmpEngine", передан: {type(engine)}')
#
#     @property
#     def protocol(self):
#         return FieldsNames.protocol_snmp
#
#     @property
#     @abc.abstractmethod
#     def snmp_config(self) -> HostSnmpConfig:
#         """ Возвращает конфигурацию snmp протокола контроллера (ug405 | stcip | ...) """
#
#     @classmethod
#     def _get_parser(cls, *args, **kwargs):
#         return cls.parser_class(*args, **kwargs)
#
#     @property
#     def request_sender(self) -> AsyncSnmpRequests:
#         return self._request_sender
#
#     def _set_varbinds_for_request(self, varbinds: T_Varbinds):
#         self._varbinds_for_request = varbinds
#
#     def _reset_varbinds_for_request(self):
#         self._varbinds_for_request = None
#
#     def _set_current_request_method(self, method: Callable):
#         self._request_method = method
#
#     def _reset_current_request_method(self):
#         self._request_method = None
#
#     def _set_varbinds_and_method_for_request(self, varbinds: T_Varbinds, method: Callable):
#         self._varbinds_for_request = varbinds
#         self._request_method = method
#
#     def _reset_varbinds_and_method_for_request(self):
#         self._reset_varbinds_for_request()
#         self._reset_current_request_method()
#
#     def _check_snmp_response_errors_and_add_to_host_data_if_has(self):
#         """
#             self.__response[ResponseStructure.ERROR_INDICATION] = error_indication: errind.ErrorIndication,
#             self.__response[ResponseStructure.ERROR_STATUS] = error_status: Integer32 | int,
#             self.__response[ResponseStructure.ERROR_INDEX] = error_index: Integer32 | int
#         """
#         if self.last_response[SnmpResponseStructure.ERROR_INDICATION] is not None:
#             self.add_data_to_data_response_attrs(self.last_response[SnmpResponseStructure.ERROR_INDICATION])
#         elif (
#             self.last_response[SnmpResponseStructure.ERROR_STATUS]
#             or self.last_response[SnmpResponseStructure.ERROR_INDEX]
#         ):
#             self.add_data_to_data_response_attrs(BadControllerType())
#         return bool(self.response_errors)
#
#     async def _make_request_and_build_response(self) -> Self:
#         """
#         Осуществляет вызов соответствующего snmp-запроса и передает
#         self.__parse_response_all_types_requests полученный ответ для парса response.
#         """
#         self.response.reset()
#         self.last_response = await self._request_method(varbinds=self._varbinds_for_request)
#
#         if self._check_snmp_response_errors_and_add_to_host_data_if_has():
#             return self
#
#         self._parser.parse(
#             varbinds=self.last_response[SnmpResponseStructure.VAR_BINDS],
#             config=self._parse_method_config
#         )
#
#         if not self._parser.data_for_response:
#             self.add_data_to_data_response_attrs(BadControllerType())
#             self._reset_varbinds_and_method_for_request()
#             return self
#
#         self.add_data_to_data_response_attrs(data=self._parser.data_for_response)
#         self._reset_varbinds_and_method_for_request()
#         return self


class Ug405Hosts(SnmpHost, ScnConverterMixin):

    def __init__(
            self,
            *,
            ipv4: str = None,
            engine=None,
            host_id=None,
            scn=None
    ):
        super().__init__(ipv4=ipv4, engine=engine, host_id=host_id)
        self.scn_as_chars = scn
        self.scn_as_ascii_string = self._get_scn_as_ascii_from_scn_as_chars_attr()

    @property
    def snmp_config(self) -> HostSnmpConfig:
        """
        Возвращает конфигурацию конкретной реализации snmp(Stcip, Ug405 ...)
        """
        return snmp_config.ug405

    @property
    @abc.abstractmethod
    def _method_for_get_scn(self) -> Callable:
        """ Snmp-метод для получения scn """

    @property
    @abc.abstractmethod
    def _operation_mode_dependency(self) -> bool:
        """
        Возвращает True, если для set-запросов требуется
        предварительная проверка и установка utcType2OperationMode,
        иначе False.
        """

    async def _get_dependency_data_and_add_error_if_has(self):
        """
        Получает и обрабатывает зависимость для snmp-запросов.
        В данной реализации получение scn и установка в соответствующие атрибуты.
        """

        self.last_response = await self._method_for_get_scn(varbinds=[CommonVarbindsUg405.site_id_varbind])

        if self._check_response_errors_and_add_to_response_entity_if_has():
            return
        try:
            self._set_scn_from_response()
        except BadControllerType as e:
            self.add_data_to_data_response_attrs(e)

    async def _collect_data_and_send_snmp_request_ug405(
            self,
            *,
            method: Callable,
            varbinds_generate_method: Callable,
            value: int | str = None,
            parse_method: Callable = None,
    ):
        """
        Основной метод-драйвер для формирования snmp запроса.
        """

        await self._get_dependency_data_and_add_error_if_has()
        if self.response_errors:
            return self

        if method == self._request_sender.snmp_get:
            self._set_varbinds_and_method_for_request(
                varbinds=varbinds_generate_method(self.scn_as_ascii_string),
                method=method
            )
            # self.set_varbinds_for_request(varbinds_generate_method(self.scn_as_ascii_string))
        elif method == self._request_sender.snmp_set:

            if self._operation_mode_dependency:
                await self.set_operation_mode3_across_operation_mode2()
                if self._check_response_errors_and_add_to_response_entity_if_has():
                    return self

            self._set_varbinds_and_method_for_request(
                varbinds=varbinds_generate_method(self.scn_as_ascii_string, value),
                method=method
            )
        else:
            raise TypeError

        if callable(parse_method):
            self._parse_method_config = parse_method()
        else:
            self._parse_method_config = self._get_default_processed_config()

        return await self._make_request_and_build_response()

    async def get_states(self) -> Self:
        """
        Отравляет snmp-get запрос и формирует текущее состояние работы
        дорожного контроллера.
        :return: Self.
        """
        return await self._collect_data_and_send_snmp_request_ug405(
            method=self._request_sender.snmp_get,
            varbinds_generate_method=self.varbinds.get_varbinds_current_states,
            value=None,
            parse_method=self._get_parser_config_with_remove_scn_from_oid_and_pretty_parsed_varbinds
        )

    async def set_stage(self, value: int) -> Self:
        """
        Отравляет snmp-set запрос на установку фазы дорожного контроллера.
        :param value: Номер фазы в десятичном представлении.
        :return:
        """
        return await self._collect_data_and_send_snmp_request_ug405(
            method=self._request_sender.snmp_set,
            varbinds_generate_method=self.varbinds.get_varbinds_set_stage,
            value=value,
            parse_method=self._get_default_processed_config
        )

    async def set_operation_mode(self, value: int) -> None:
        """
        Отправляет запрос на установку utcType2OperationMode.
        :param value: Значение utcType2OperationMode.
        :return: None
        """
        self.last_response = await self._request_sender.snmp_set(
            varbinds=[CommonVarbindsUg405.get_operation_mode_varbinds(value)]
        )

    async def set_operation_mode1(self):
        """
        Отправляет запрос на установку utcType2OperationMode = 1.
        :return: None
        """
        await self.set_operation_mode(1)

    async def set_operation_mode2(self):
        """
        Отправляет запрос на установку utcType2OperationMode = 2.
        :return: None
        """
        await self.set_operation_mode(2)

    async def set_operation_mode3(self):
        """
        Отправляет запрос на установку utcType2OperationMode = 3.
        :return: None
        """
        await self.set_operation_mode(3)

    async def set_operation_mode3_across_operation_mode2(self):
        """
        Устанавливает utcType2OperationMode = 3.
        Перед установкой проверяет текущее значение utcType2OperationMode.

        -- Если utcType2OperationMode = 1:
           то устанавливает utcType2OperationMode = 2, затем utcType2OperationMode = 3
        -- Если utcType2OperationMode = 2:
           то устанавливает utcType2OperationMode = 3
        -- Если utcType2OperationMode = 3:
           сразу возвращает True.

        :return: True, utcType2OperationMode = 3, иначе False.
        """

        self.last_response = await self._request_sender.snmp_get(
            varbinds=[CommonVarbindsUg405.operation_mode_varbind]
        )
        if self._check_response_errors_and_add_to_response_entity_if_has():
            return False

        op_mode = str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][1])
        if op_mode == '3':
            return True

        if op_mode == '1':
            await self.set_operation_mode2()
            if self._check_response_errors_and_add_to_response_entity_if_has():
                return False
            await self.set_operation_mode3()
            if self._check_response_errors_and_add_to_response_entity_if_has():
                return False
        elif op_mode == '2':
            await self.set_operation_mode3()
            if self._check_response_errors_and_add_to_response_entity_if_has():
                return False

        self.last_response = await self._request_sender.snmp_get(
            varbinds=[CommonVarbindsUg405.operation_mode_varbind]
        )

        if self._check_response_errors_and_add_to_response_entity_if_has():
            return False
        return str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][1]) == '3'

    def _get_scn_as_ascii_from_scn_as_chars_attr(self) -> str | None:
        return self.get_scn_as_ascii_from_scn_as_chars_attr(self.scn_as_chars)

    def _get_scn_as_chars_from_scn_as_ascii(self) -> str:
        return self.get_scn_as_ascii_from_scn_as_chars_attr(self.scn_as_ascii_string)

    def _set_scn_from_response(self):
        raise NotImplementedError()

    def _get_parser_config_with_remove_scn_from_oid_and_pretty_parsed_varbinds(self):
        return ConfigsParser(
            extras=True,
            oid_handler=build_func_with_remove_scn(self.scn_as_ascii_string, get_val_as_str),
            val_oid_handler=pretty_print,
            oid_name_by_alias=True,
            host_protocol=FieldsNames.protocol_ug405
        )

    def _get_default_processed_config(self):
        return default_processing_ug405_config


class StcipHosts(SnmpHost):

    @property
    def snmp_config(self) -> HostSnmpConfig:
        return snmp_config.stcip

    async def get_states(self):
        self._parse_method_config = pretty_processing_stcip_config
        self._set_varbinds_and_method_for_request(
            varbinds=self.varbinds.get_varbinds_current_states(),
            method=self._request_sender.snmp_get
        )
        return await self._make_request_and_build_response()

    async def set_stage(self, value: int):
        self._parse_method_config = default_processing_stcip
        self._set_varbinds_and_method_for_request(
            varbinds=self.varbinds.get_varbinds_set_stage(value),
            method=self._request_sender.snmp_set
        )
        return await self._make_request_and_build_response()

    async def get_current_stage(self):
        self._parse_method_config = pretty_processing_stcip_without_extras
        self._set_varbinds_and_method_for_request(
            varbinds=self.varbinds.get_stage_varbinds,
            method=self._request_sender.snmp_get
        )
        return await self._make_request_and_build_response()


class SwarcoStcip(StcipHosts):

    _parser_class = ParsersVarbindsSwarco
    varbinds = swarco_stcip_varbinds


class PotokS(StcipHosts):

    _parser_class = ParsersVarbindsPotokS
    varbinds = potok_stcip_varbinds


class PotokP(Ug405Hosts):

    _parser_class = ParsersVarbindsPotokP
    varbinds = potok_ug405_varbinds

    @property
    def _method_for_get_scn(self) -> Callable:
        return self._request_sender.snmp_get

    @property
    def _operation_mode_dependency(self) -> bool:
        return False

    def _set_scn_from_response(self) -> None | BadControllerType:
        try:
            self.scn_as_chars = str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][1])
            self.scn_as_ascii_string = self._get_scn_as_ascii_from_scn_as_chars_attr()
        except IndexError:
            raise  BadControllerType()
        return None


class PeekUg405(Ug405Hosts):

    _parser_class = ParsersVarbindsPeek
    varbinds = peek_ug405_varbinds

    @property
    def _method_for_get_scn(self) -> Callable:
        return self._request_sender.snmp_get_next

    @property
    def _operation_mode_dependency(self) -> bool:
        return True

    def _set_scn_from_response(self) -> None | BadControllerType:
        try:
            oid = str(self.last_response[SnmpResponseStructure.VAR_BINDS][0][0])
            self.scn_as_ascii_string = oid.replace(oids.Oids.utcReplyGn , '')
            self.scn_as_chars = self.get_scn_as_chars_from_scn_as_ascii(self.scn_as_ascii_string)
        except IndexError:
            raise  BadControllerType()
        return None


async def main():

    obj = PotokS(ipv4='10.179.88.113', host_id='3281')
    # obj = SwarcoStcip(ip_v4='10.179.20.129')
    # obj = SwarcoStcip(ip_v4='10.179.68.105')
    # obj = SwarcoStcip(ip_v4='10.179.57.1')
    # obj = SwarcoStcip(ip_v4='10.179.61.33', host_id='3205')
    # obj = PotokS(ip_v4='10.179.68.177',)
    # obj = SwarcoStcip(ipv4='10.179.108.177', host_id='2851', engine=SnmpEngine())

    # obj = PotokP(ip_v4='10.179.69.65', host_id='2600')
    # obj = PotokP(ip_v4='10.179.56.105', host_id='155')
    # obj = PotokP(ipv4='10.179.108.129', host_id='2822')
    # obj = PotokP(ipv4='10.179.69.129', host_id='2954')
    # obj.set_driver()
    # obj = SwarcoStcip(ipv4='10.179.89.225', host_id='3584')

    # obj.ip_v4 = '10.179.20.129'

    # obj = PeekUg405(ipv4='10.179.67.73')

    obj = TempSwarco(ipv4='10.179.20.129', engine=snmp_engine)

    start_time = time.time()

    res = await obj.get_states_request()

    # print(obj.response_as_dict)
    # print(json.dumps(obj.response_as_dict, indent=4))


    """set command test"""

    # res = await obj.set_stage(2)

    # print(res.response_as_dict)

    print(res)
    print(f'время составло: {time.time() - start_time}')

    return obj.response


if __name__ == '__main__':

    asyncio.run(main())
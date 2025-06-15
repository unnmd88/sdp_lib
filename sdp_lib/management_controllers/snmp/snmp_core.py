import abc
import asyncio
import functools
import time
from abc import abstractmethod
from dataclasses import dataclass
from functools import cached_property
from typing import (
    Self,
    Type
)
from collections.abc import (
    Callable,
    Awaitable
)

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts_core import (
    Host,
    ResponseEntity
)
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.processing_methods import (
    get_val_as_str,
    pretty_print,
    build_func_with_remove_scn
)
from sdp_lib.management_controllers.parsers.snmp_parsers.varbinds_parsers import (
    pretty_processing_stcip_config,
    ConfigsParser,
    ParsersVarbindsSwarco,
    ParsersVarbindsPotokS,
    ParsersVarbindsPotokP,
    ParsersVarbindsPeek,
    default_processing_ug405_config,
    default_processing_stcip_config,
    pretty_processing_stcip_config_without_extras
)
from sdp_lib.management_controllers.snmp import (
    oids,
    snmp_utils
)
from sdp_lib.management_controllers.structures import SnmpResponseStructure
from sdp_lib.management_controllers.snmp.set_commands import SnmpEntity
from sdp_lib.management_controllers.snmp.snmp_utils import (
    ScnConverterMixin,
    HostSnmpConfig,
    VarbSwarco,
    VarbPotokS,
    VarbPotokP,
    VarbPeek
)
from sdp_lib.management_controllers.snmp.snmp_requests import (
    AsyncSnmpRequests,
    snmp_engine,
    SnmpEngine
)
from sdp_lib.management_controllers.snmp.snmp_utils import (
    swarco_stcip_varbinds,
    potok_stcip_varbinds,
    potok_ug405_varbinds,
    peek_ug405_varbinds, CommonVarbindsUg405
)


def ug405_dependency(
        type_request_entity: SnmpEntity,
        varbinds_builder_method: Callable
):
    def wrapper(func: Callable):
        @functools.wraps(func)
        async def wrapped(instance, value=None, *args, **kwargs):
            # print(f'dependency_varbinds: {dependency_varbinds}')
            await instance.get_scn_and_add_error_if_has()
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


@dataclass(slots=True)
class RequestConfig:
    parser: ParsersVarbindsSwarco | ParsersVarbindsPotokS | ParsersVarbindsPotokP | ParsersVarbindsPeek
    snmp_request_coro: Awaitable = None
    parser_config: ConfigsParser | None = None
    create_response_entity: bool = True
    # snmp_method: Callable | None= None
    # varbinds: T_Varbinds | None= None
    timeout: float = 1
    retries: int = 0

    def load_snmp_request_coro(self, coro: Awaitable):
        self.snmp_request_coro = coro


class SnmpHost(Host):
    """
    Класс абстрактного хоста, в котором реализована логика формирования snmp-запросов,
    получение и обработка snmp-ответов.
    """

    _parser_class: Type[ParsersVarbindsSwarco | ParsersVarbindsPotokS | ParsersVarbindsPotokP | ParsersVarbindsPeek]
    _varbinds: VarbSwarco | VarbPotokS | VarbPotokP | VarbPeek
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
        self._parser = self._parser_class()
        self._request_config: RequestConfig = RequestConfig(parser=self._parser)
        self._get_states_request_config: RequestConfig | None = None

    @cached_property
    @abc.abstractmethod
    def snmp_config(self) -> HostSnmpConfig:
        """ Возвращает конфигурацию snmp протокола контроллера (ug405 | stcip | ...) """
        ...

    @classmethod
    def _get_parser(cls):
        return cls._parser_class

    @property
    def request_sender(self) -> AsyncSnmpRequests:
        return self._request_sender

    def reset_states_request_config(self):
        self._get_states_request_config = None

    async def _make_request_and_load_response_to_storage(self, request_config: RequestConfig) -> Self:
        """
        Осуществляет вызов соответствующего snmp-запроса и передает
        self.__parse_response_all_types_requests полученный ответ для парса response.
        """
        # self._tmp_response = await request_config.snmp_method(varbinds=request_config.varbinds)
        self._tmp_response = await request_config.snmp_request_coro
        self._check_response_errors_and_add_to_response_entity_if_has()
        if request_config.create_response_entity:
            self._parser.load_config_parser(request_config.parser_config)
            self._response_storage.storage_raw_responses.append(
                ResponseEntity(
                    raw_data=self._tmp_response[SnmpResponseStructure.VAR_BINDS],
                    name=FieldsNames.snmp_varbinds,
                    parser=self._parser
                )
            )
            # DEBUG
            self._response_storage.build_response_as_dict_from_raw_data_responses(self.ip_v4)
        return self

    def _check_response_errors_and_add_to_response_entity_if_has(self) -> bool:
        """
        self._response[ResponseStructure.ERROR_INDICATION] = error_indication: errind.ErrorIndication,
        self._response[ResponseStructure.ERROR_STATUS] = error_status: Integer32 | int,
        self._response[ResponseStructure.ERROR_INDEX] = error_index: Integer32 | int
        :return True, при наличии ошибки запроса(error_indication | error_status | error_index):
        """
        if self._tmp_response[SnmpResponseStructure.VAR_BINDS]:
            return False
        self._response_storage.put_errors(
            self._tmp_response[SnmpResponseStructure.ERROR_INDICATION]
            or BadControllerType()
        )
        return True


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

    @cached_property
    def snmp_config(self) -> HostSnmpConfig:
        """
        Возвращает конфигурацию конкретной реализации snmp(Stcip, Ug405 ...)
        """
        return snmp_utils.ug405_config

    @property
    @abstractmethod
    def _method_for_request_scn(self) -> Callable:
        """ Snmp-метод для получения scn """
        ...

    @property
    @abstractmethod
    def has_operation_mode_dependency(self) -> bool:
        """
        Возвращает True, если для set-запросов требуется
        предварительная проверка и установка utcType2OperationMode,
        иначе False.
        """
        raise NotImplementedError()

    @abstractmethod
    def _set_scn_from_response(self):
        """ Устанавливает scn из snmp-response в соответствующие атрибуты. """
        ...

    async def get_scn_and_add_error_if_has(self) -> bool:
        """
        Получает и обрабатывает зависимость для snmp-запросов.
        В данной реализации получение scn и установка в соответствующие атрибуты.
        """
        if self.scn_as_ascii_string:
            return True

        self._tmp_response = await self._method_for_request_scn(varbinds=[CommonVarbindsUg405.site_id_varbind])
        if self._check_response_errors_and_add_to_response_entity_if_has():
            return False
        try:
            self._set_scn_from_response()
            return True
        except BadControllerType as e:
            self.reset_scn_attrs()
            self._response_storage.put_errors(e)
        return False

    def _get_scn_as_ascii_from_scn_as_chars_attr(self) -> str | None:
        return self.get_scn_as_ascii_from_scn_as_chars_attr(self.scn_as_chars)

    def _get_scn_as_chars_from_scn_as_ascii(self) -> str:
        return self.get_scn_as_ascii_from_scn_as_chars_attr(self.scn_as_ascii_string)

    def _get_config_parser_with_remove_scn_from_oid_and_pretty_parsed_varbinds(self):
        return ConfigsParser(
            extras=True,
            oid_handler=build_func_with_remove_scn(self.scn_as_ascii_string, get_val_as_str),
            val_oid_handler=pretty_print,
            oid_name_by_alias=True,
            host_protocol=FieldsNames.protocol_ug405
        )

    def reset_scn_attrs(self):
        self.scn_as_chars = None
        self.scn_as_ascii_string = None

    async def set_operation_mode3_across_operation_mode2_and_add_error_if_has(self) -> bool:
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

        op_mode_varbind = (self._varbinds.operation_mode_varbind, )
        self._tmp_response = await self._request_sender.snmp_get(varbinds=op_mode_varbind)
        if self._check_response_errors_and_add_to_response_entity_if_has():
            return False
        op_mode = int(self._tmp_response[SnmpResponseStructure.VAR_BINDS][0][1].prettyPrint())
        if op_mode == 3:
            return True

        for operation_mode_set_command in range(op_mode, 3):
            self._tmp_response = await self._request_sender.snmp_set(
                varbinds=[self._varbinds.get_operation_mode_varbinds(op_mode + 1)]
            )
            if self._check_response_errors_and_add_to_response_entity_if_has():
                return False

        self._tmp_response = await self._request_sender.snmp_get(varbinds=op_mode_varbind)
        if self._check_response_errors_and_add_to_response_entity_if_has():
            return False
        return self._tmp_response[SnmpResponseStructure.VAR_BINDS][0][1].prettyPrint() == '3'

    async def collect_dependency_and_add_error_if_has(self, *coros: Awaitable) -> bool:
        async with asyncio.TaskGroup() as tg:
            response = [tg.create_task(coro) for coro in coros]
        return all(t.result() for t in response)

    async def collect_scn_dependency_and_add_error_if_has(self) -> bool:
        return await self.collect_dependency_and_add_error_if_has(self.get_scn_and_add_error_if_has())

    async def collect_scn_and_operation_mode_dependency_and_add_error_if_has(self) -> bool:
        return await self.collect_dependency_and_add_error_if_has(
            self.get_scn_and_add_error_if_has(),
            self.set_operation_mode3_across_operation_mode2_and_add_error_if_has()
        )

    async def set_operation_mode(self, value: int) -> bool:
        """
        Отправляет запрос на установку utcType2OperationMode.
        :param value: Значение utcType2OperationMode.
        :return: None
        """
        self._tmp_response = await self._request_sender.snmp_set(
            varbinds=[self._varbinds.get_operation_mode_varbinds(value)]
        )
        if self._tmp_response[SnmpResponseStructure.VAR_BINDS]:
            return True
        return False

    async def set_operation_mode1(self) -> bool:
        """
        Отправляет запрос на установку utcType2OperationMode = 1.
        :return: True, если отправка значения успешна, иначе False
        """
        return await self.set_operation_mode(1)

    async def set_operation_mode2(self) -> bool:
        """
        Отправляет запрос на установку utcType2OperationMode = 2.
        :return: True, если отправка значения успешна, иначе False
        """
        return await self.set_operation_mode(2)

    async def set_operation_mode3(self):
        """
        Отправляет запрос на установку utcType2OperationMode = 3.
        :return: None
        """
        return await self.set_operation_mode(3)

    async def get_states(self) -> Self:
        """
        Отравляет snmp-get запрос и формирует текущее состояние работы
        дорожного контроллера.
        :return: Self.
        """
        if self._get_states_request_config is not None:
            self._get_states_request_config.load_snmp_request_coro(
                self._request_sender.snmp_get(self._varbinds.get_varbinds_current_states(self.scn_as_ascii_string))
            )
            return await self._make_request_and_load_response_to_storage(self._get_states_request_config)

        scn_success = await self.get_scn_and_add_error_if_has()
        if not scn_success:
            return self

        self._get_states_request_config = RequestConfig(
            parser=self._parser,
            snmp_request_coro=self._request_sender.snmp_get(
                self._varbinds.get_varbinds_current_states(self.scn_as_ascii_string)
            ),
            # snmp_method=self._request_sender.snmp_get,
            parser_config=self._get_config_parser_with_remove_scn_from_oid_and_pretty_parsed_varbinds(),
            # varbinds=self._varbinds.get_varbinds_current_states(self.scn_as_ascii_string)
        )
        return await self._make_request_and_load_response_to_storage(self._get_states_request_config)

    async def set_stage(self, value: int) -> Self:
        """
        Отравляет snmp-set запрос на установку фазы дорожного контроллера.
        :param value: Номер фазы в десятичном представлении.
        :return:
        """
        value = int(value)
        if not 0 <= value <= self._varbinds.max_stage:
            raise ValueError(f'Недопустимый номер фазы: {self.value}')

        if value > 0:
            if self.has_operation_mode_dependency:
                success = await self.collect_scn_and_operation_mode_dependency_and_add_error_if_has()
            else:
                success = await self.collect_scn_dependency_and_add_error_if_has()
            if not success:
                return self
        self._request_config.parser = self._parser
        self._request_config.load_snmp_request_coro(
            self._request_sender.snmp_set(self._varbinds.get_varbinds_set_stage(self.scn_as_ascii_string, value))
        )
        self._request_config.parser_config = default_processing_ug405_config

        print(self._request_config)

        return await self._make_request_and_load_response_to_storage(self._request_config)


class StcipHosts(SnmpHost):

    def __init__(
            self,
            *,
            ipv4: str = None,
            engine=None,
            host_id=None,
    ):
        super().__init__(ipv4=ipv4, engine=engine, host_id=host_id)
        self._get_states_request_config = RequestConfig(
                parser=self._parser,
                parser_config=pretty_processing_stcip_config,
                create_response_entity=True
            )

    @cached_property
    def snmp_config(self) -> HostSnmpConfig:
        return snmp_utils.stcip_config

    async def get_states(self):
        self._get_states_request_config.load_snmp_request_coro(
            self._request_sender.snmp_get(self._varbinds.get_varbinds_current_states())
        )
        return await self._make_request_and_load_response_to_storage(self._get_states_request_config)

    async def set_stage(self, value: int):
        self._parse_method_config = default_processing_stcip_config
        self._request_config.snmp_method = self._request_sender.snmp_set
        self._set_varbinds_and_method_for_request(
            varbinds=self._varbinds.get_varbinds_set_stage(value),
            method=self._request_sender.snmp_set
        )
        return await self._make_request_and_build_response()

    async def get_current_stage(self):
        self._parse_method_config = pretty_processing_stcip_config_without_extras
        self._set_varbinds_and_method_for_request(
            varbinds=self._varbinds.get_stage_varbinds,
            method=self._request_sender.snmp_get
        )
        return await self._make_request_and_build_response()


class SwarcoStcip(StcipHosts):

    _parser_class = ParsersVarbindsSwarco
    _varbinds = swarco_stcip_varbinds


class PotokS(StcipHosts):

    _parser_class = ParsersVarbindsPotokS
    _varbinds = potok_stcip_varbinds


class PotokP(Ug405Hosts):

    _parser_class = ParsersVarbindsPotokP
    _varbinds = potok_ug405_varbinds

    @cached_property
    def _method_for_request_scn(self) -> Callable:
        return self._request_sender.snmp_get

    @cached_property
    def has_operation_mode_dependency(self) -> bool:
        return False

    def _set_scn_from_response(self) -> None | BadControllerType:
        try:
            self.scn_as_chars = str(self._tmp_response[SnmpResponseStructure.VAR_BINDS][0][1])
            self.scn_as_ascii_string = self._get_scn_as_ascii_from_scn_as_chars_attr()
        except IndexError:
            raise BadControllerType()
        return None


class PeekUg405(Ug405Hosts):

    _parser_class = ParsersVarbindsPeek
    _varbinds = peek_ug405_varbinds

    @cached_property
    def _method_for_request_scn(self) -> Callable:
        return self._request_sender.snmp_get_next

    @cached_property
    def has_operation_mode_dependency(self) -> bool:
        return True

    def _set_scn_from_response(self) -> None | BadControllerType:
        try:
            oid = str(self._tmp_response[SnmpResponseStructure.VAR_BINDS][0][0])
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
    obj = PotokP(ipv4='10.179.69.129', host_id='2954', engine=snmp_engine)
    # obj = PotokS(ipv4='10.179.24.153', host_id='205', engine=snmp_engine)
    # obj.set_driver()
    # obj = SwarcoStcip(ipv4='10.179.89.225', host_id='3584')

    # obj.ip_v4 = '10.179.20.129'

    # obj = PeekUg405(ipv4='10.179.67.73')

    # obj = SwarcoStcip(ipv4='10.179.20.129', engine=snmp_engine, host_id='2405')

    # obj = PeekUg405(ipv4='10.45.154.19', host_id='laba', engine=snmp_engine)


    # start_time = time.time()
    # res = await obj.set_stage(2)

    while True:
        start_time = time.time()
        res = await obj.get_states()
        # res = await obj.set_stage(5)
        print(res.response)
        print(f'время составло: {time.time() - start_time}')
        await asyncio.sleep(2)

    # print(obj.response_as_dict)
    # print(json.dumps(obj.response_as_dict, indent=4))


    """set command test"""

    # res = await obj.set_stage(2)

    # print(res.response_as_dict)

    print(res)
    print(res.response)
    print(res.ip_v4)
    print(f'время составло: {time.time() - start_time}')

    return obj.response


if __name__ == '__main__':

    asyncio.run(main())
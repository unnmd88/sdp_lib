import abc
import asyncio
import functools
import itertools
import json
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
    Awaitable, Sequence, Coroutine, MutableSequence
)

from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.hosts_core import (
    Host,
    ResponseEntity, RequestResponse
)
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.snmp_parsers.processing_methods import (
    get_val_as_str,
    pretty_print,
    build_func_with_remove_scn
)
from sdp_lib.management_controllers.parsers.snmp_parsers.varbinds_parsers import (
    pretty_processing_stcip_parser_config,
    ParserConfig,
    ParsersVarbindsSwarco,
    ParsersVarbindsPotokS,
    ParsersVarbindsPotokP,
    ParsersVarbindsPeek,
    default_processing_ug405_parser_config,
    default_processing_stcip_parser_config,
    pretty_processing_stcip_parser_config_without_extras
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
    VarbPeek, ScnUg405
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
            await instance.get_scn_from_host_and_set_to_attr()
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
    parser_config: ParserConfig | None = None
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
        self._request_response_default = RequestResponse(
            protocol=self.protocol,
            parser=self._parser_class(),
            add_to_response_storage=True
        )
        self._request_response_get_states = RequestResponse(
            protocol=self.protocol,
            name='get_state',
            add_to_response_storage=True,
            parser=self._parser_class()
        )
        self._get_states_parser_config: ParserConfig = None

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

    async def _make_request(self, request_response: RequestResponse) -> Self:
        """
        Осуществляет вызов соответствующего snmp-запроса и передает
        self.__parse_response_all_types_requests полученный ответ для парса response.
        """
        # self._tmp_response = await request_config.snmp_method(varbinds=request_config.varbinds)
        self._tmp_response = await request_response.coro
        error = self._check_tmp_response_errors()
        print(f'error: {error}')
        print(f'self._tmp_response: {self._tmp_response}')
        if error:
            request_response.load_error(error)
            self._data_storage.put(request_response)
            return self
        request_response.load_raw_response(self._tmp_response[SnmpResponseStructure.VAR_BINDS])
        self._data_storage.put(request_response)
        return self

    def _check_tmp_response_errors(self) -> None | str | Exception:
        """
        self._response[ResponseStructure.ERROR_INDICATION] = error_indication: errind.ErrorIndication,
        self._response[ResponseStructure.ERROR_STATUS] = error_status: Integer32 | int,
        self._response[ResponseStructure.ERROR_INDEX] = error_index: Integer32 | int
        :return None если нет ошибок в response.
                При наличии ошибки запроса(error_indication | error_status | error_index):
                Экземпляр Exception или текст ошибки в строковом представлении.
        """
        if self._tmp_response[SnmpResponseStructure.VAR_BINDS]:
            return None
        return self._tmp_response[SnmpResponseStructure.ERROR_INDICATION] or BadControllerType()



class Ug405Hosts(SnmpHost):

    def __init__(
            self,
            *,
            ipv4: str = None,
            engine=None,
            host_id=None,
            scn=''
    ):
        super().__init__(ipv4=ipv4, engine=engine, host_id=host_id)
        self._seconds_freshness_scn: float = 60
        self._timestamp_set_scn: float = 0
        self._scn = ScnUg405(scn)
        self._dependencies_coroutines: Sequence[Coroutine] = []
        self._get_states_parser_config = ParserConfig(
            extras=True,
            val_oid_handler=pretty_print,
            oid_name_by_alias=True,
            host_protocol=FieldsNames.protocol_ug405
        )


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
    def _get_scn_as_chars_from_tmp_response(self):
        """ Устанавливает scn из snmp-response в соответствующие атрибуты. """
        ...

    @abstractmethod
    def get_management_coroutines_dependency(self) -> MutableSequence[Coroutine]:
        """
        Возвращает MutableSequence с корутинами,
        которые необходимо выполнить перед началом управления контроллером
        """
        ...

    def set_freshness_scn_time_in_seconds(self, seconds: float):
        self._seconds_freshness_scn = float(seconds)

    def get_seconds_freshness_scn(self) -> float:
        return self._seconds_freshness_scn

    def check_scn_is_fresh(self) -> bool:
        if self._seconds_freshness_scn == 0 or time.time() - self._timestamp_set_scn < self._seconds_freshness_scn:
            return True
        return False

    def set_scn(self, value: Sequence[str] | str):
        self._scn.refresh(value)

    def reset_scn(self):
        self._scn.reset_scn_to_empty_string()

    async def get_scn_from_host_and_set_to_attr(self) -> None | str | Exception:
        """
        Получает scn из соответствующего oid и устанавливает в соответствующий атрибут.
        :return : При успешной установке scn возвращает None, иначе возвращает текст ошибки.
        """
        if self._scn.scn_as_ascii and self.check_scn_is_fresh():
            print(f'SCN IS FRESH!!!')
            return None
        print(f'SCN IS ROTTEN...')

        self._tmp_response = await self._method_for_request_scn(varbinds=[self._varbinds.site_id_varbind])
        response_error = self._check_tmp_response_errors()
        if response_error is None:
            self._scn.refresh(self._get_scn_as_chars_from_tmp_response())
            self._timestamp_set_scn = time.time()
        else:
            self.reset_scn()
        return response_error

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

    async def set_operation_mode3_across_operation_mode2_and_add_error_if_has(self) -> None | str | Exception:
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
        error = self._check_tmp_response_errors()
        if error:
            return error
        op_mode = int(self._tmp_response[SnmpResponseStructure.VAR_BINDS][0][1].prettyPrint())
        if op_mode == 3:
            return None

        for operation_mode_set_command in range(op_mode, 3):
            self._tmp_response = await self._request_sender.snmp_set(
                varbinds=[self._varbinds.get_operation_mode_varbinds(op_mode + 1)]
            )
            error = self._check_tmp_response_errors()
            if error is not None:
                return error

        self._tmp_response = await self._request_sender.snmp_get(varbinds=op_mode_varbind)
        error = self._check_tmp_response_errors()
        if error:
            return False
        assert self._tmp_response[SnmpResponseStructure.VAR_BINDS][0][1].prettyPrint() == '3'
        return None

    async def collect_dependencies_and_load_errors_if_has(
            self,
            coroutines: Sequence[Coroutine],
            request_response: RequestResponse
    ) -> RequestResponse:
        async with asyncio.TaskGroup() as tg:
            finished_tasks = [tg.create_task(coro) for coro in coroutines]
        for task in finished_tasks:
            error = task.result()
            if error is not None:
                request_response.load_error(error)
        return request_response

    async def get_states(self) -> Self:
        """
        Отравляет snmp-get запрос и формирует текущее состояние работы
        дорожного контроллера.
        :return: Self.
        """
        self._request_response_get_states.reset_data()
        self._request_response_get_states = await self.collect_dependencies_and_load_errors_if_has(
            [self.get_scn_from_host_and_set_to_attr()], self._request_response_get_states
        )
        if self._request_response_get_states.errors:
            self._data_storage.put(self._request_response_get_states)
            return self

        # error = await self.get_scn_from_host_and_set_to_attr()
        # if error is not None:
        #     self._request_response_get_states.load_error(error)
        #     return self

        self._get_states_parser_config.set_oid_handler(
            build_func_with_remove_scn(self._scn.scn_as_ascii, get_val_as_str)
        )
        self._request_response_get_states.parser.load_config_parser(self._get_states_parser_config)
        self._request_response_get_states.load_coro(
            self._request_sender.snmp_get(self._varbinds.get_varbinds_current_states(self._scn.scn_as_ascii))
        )
        return await self._make_request(self._request_response_get_states)

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
            self._dependencies_coroutines = [self.get_scn_from_host_and_set_to_attr()]
            self._dependencies_coroutines += self.get_management_coroutines_dependency()
            self._request_response_default = await self.collect_dependencies_and_load_errors_if_has(
                self._dependencies_coroutines, self._request_response_default
            )
        if self._request_response_default.errors:
            self._data_storage.put(self._request_response_default)
            return self
        self._request_response_default.load_coro(
            self._request_sender.snmp_set(self._varbinds.get_varbinds_set_stage(self._scn.scn_as_ascii, value))
        )
        self._request_response_default.parser.load_config_parser(default_processing_ug405_parser_config)
        return await self._make_request(self._request_response_default)


class StcipHosts(SnmpHost):

    def __init__(
            self,
            *,
            ipv4: str = None,
            engine=None,
            host_id=None,
    ):
        super().__init__(ipv4=ipv4, engine=engine, host_id=host_id)
        self._get_states_parser_config = pretty_processing_stcip_parser_config
        self._request_response_get_states.parser.load_config_parser(self._get_states_parser_config)

    @cached_property
    def snmp_config(self) -> HostSnmpConfig:
        return snmp_utils.stcip_config

    async def get_states(self):
        self._request_response_get_states.reset_data()
        self._request_response_get_states.load_coro(
            self._request_sender.snmp_get(self._varbinds.get_varbinds_current_states())
        )
        return await self._make_request(self._request_response_get_states)

    async def set_stage(self, value: int):
        self._parse_method_config = default_processing_stcip_parser_config
        self._request_config.snmp_method = self._request_sender.snmp_set
        self._set_varbinds_and_method_for_request(
            varbinds=self._varbinds.get_varbinds_set_stage(value),
            method=self._request_sender.snmp_set
        )
        return await self._make_request_and_build_response()

    async def get_current_stage(self):
        self._parse_method_config = pretty_processing_stcip_parser_config_without_extras
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

    def _get_scn_as_chars_from_tmp_response(self) -> str:
        return str(self._tmp_response[SnmpResponseStructure.VAR_BINDS][0][1])

    def get_management_coroutines_dependency(self) -> MutableSequence[Coroutine]:
        """
        Возвращает MutableSequence с корутинами,
        которые необходимо выполнить перед началом управления контроллером
        """
        return []

class PeekUg405(Ug405Hosts):

    _parser_class = ParsersVarbindsPeek
    _varbinds = peek_ug405_varbinds

    @cached_property
    def _method_for_request_scn(self) -> Callable:
        return self._request_sender.snmp_get_next

    @cached_property
    def has_operation_mode_dependency(self) -> bool:
        return True

    def _get_scn_as_chars_from_tmp_response(self) -> str:
        oid = str(self._tmp_response[SnmpResponseStructure.VAR_BINDS][0][0])
        return oid.replace(oids.Oids.utcReplyGn , '')

        # try:
        #     oid = str(self._tmp_response[SnmpResponseStructure.VAR_BINDS][0][0])
        #     self.scn_as_ascii_string = oid.replace(oids.Oids.utcReplyGn , '')
        #     self.scn_as_chars = self.get_scn_as_chars_from_scn_as_ascii(self.scn_as_ascii_string)
        # except IndexError:
        #     raise  BadControllerType()
        # return None


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
        # res = await obj.set_stage(0)
        print(json.dumps(res.build_response_as_dict(), indent=4, ensure_ascii=False))
        print(f'время составло: {time.time() - start_time}')
        await asyncio.sleep(2)

    # print(obj.response_as_dict)
    # print(json.dumps(obj.response_as_dict, indent=4))


    """set command test"""

    # res = await obj.set_stage(2)

    # print(res.response_as_dict)

    print(json.dumps(res.build_response_as_dict(), indent=4, ensure_ascii=False))
    print(f'время составло: {time.time() - start_time}')

    return obj.response


if __name__ == '__main__':

    asyncio.run(main())
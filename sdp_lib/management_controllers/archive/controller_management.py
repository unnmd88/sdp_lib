""""
Модуль управления/получения данных различных типов  дорожных
контроллеров по протоколам: snmp, http, ssh
Версия: 1.0
"""
import ast
import inspect
import json
import os
from typing import Generator, Iterator, Any
import itertools
import math
from datetime import datetime
import logging
from collections.abc import Callable

from dotenv import load_dotenv
from pathlib import Path
from enum import Enum
import asyncssh
import asyncio
import paramiko
import aiohttp
from pysnmp.hlapi.asyncio import *

load_dotenv()
logger = logging.getLogger(__name__)


class AvailableControllers(Enum):
    """ Доступные типы контроллеров и команд"""
    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'


class EntityJsonResponce(Enum):
    """
    Доступные типы контроллера и команд
    """

    """ Основные свойства """
    PROTOCOL = 'protocol'
    SNMP = 'snmp'
    SSH ='ssh'
    TYPE = 'type'
    GET = 'get'
    SET = 'set'
    NUM_HOST = 'host_id'
    RESULT = 'result'
    TYPE_CONTROLLER = 'type_controller'
    TYPE_COMMAND = 'type_command'
    VALUE = 'value'
    REQUEST_ENTITY = 'request_entity'
    RESPONCE_ENTITY = 'responce_entity'
    TYPE_REQUEST = 'type_request'
    REQ_SENT_SUCCESSFULLY = 'request sent successfully'
    SUCCESS = 'success'
    RESPONCE_TIME = 'responce_time'
    REQUEST_TIME = 'request_time'
    GET_MODE = 'get_mode'


    """" Категория ошибок """
    NO_DATA_FOR_REQ = 'There is no data for the request'
    REQUEST_ERRORS = 'request_errors'
    TIMEOUT_ERROR_WEB_REQUEST_MSG = 'ConnectTimeoutError'
    NETWORK_CONNECTION_ERROR = 'There is no network connection'
    TYPE_CONTROLLER_ERROR_MSG = 'Type controller error'
    BAD_DATA_SET_REQ = 'Предоставлены некорректные данные для запроса'
    SET_VAL_TO_WEB_ERROR_MSG = 'Error setting the value on the web'

    """" raw_data """
    DATA_RESPONCE = 'raw_data'
    CURRENT_STATES = 'current_states'
    SENT_COMMANDS = 'sent_commands'
    BASIC_STATE = 'basic'
    INPUTS = 'inputs'
    USER_PARAMETERS = 'user_parameters'
    WEB_CONTENT_STATE = 'web_content'
    CURRENT_PLAN = 'current_plan'
    CURRENT_PARAM_PLAN = 'current_parameter_plan'
    CURRENT_TIME = 'current_time'
    CURRENT_CYC_TIMME = 'current_cyc'
    CURRENT_ERRORS = 'current_errors'
    CURRENT_DET_ERRORS = 'current_det_errors'
    CURRENT_STATE = 'current_state'
    CURRENT_MODE = 'current_mode'
    CURRENT_STAGE = 'current_stage'
    CURRENT_STAGE_TIME = 'current_stage_time'
    CURRENT_SYSTEM_TIME = 'system_time'
    CURRENT_STATE_BUTTONS = 'current_state_buttons'


class JsonBody(Enum):
    """
    В данном классе собраны структуры для json responce
    """

    BASE_JSON_BODY = (
        EntityJsonResponce.TYPE_CONTROLLER.value,
        EntityJsonResponce.NUM_HOST.value,
    )


class Oids(Enum):
    """
    В классе собраны оиды для ДК по протоколам STCIP и UG405
    """

    """" STCIP """
    # Command
    swarcoUTCTrafftechPhaseCommand = os.getenv('swarcoUTCTrafftechPhaseCommand')
    swarcoUTCCommandDark = os.getenv('swarcoUTCCommandDark')
    swarcoUTCCommandFlash = os.getenv('swarcoUTCCommandFlash')
    swarcoUTCTrafftechPlanCommand = os.getenv('swarcoUTCTrafftechPlanCommand')
    # Status
    swarcoUTCStatusEquipment = os.getenv('swarcoUTCStatusEquipment')
    swarcoUTCTrafftechPhaseStatus = os.getenv('swarcoUTCTrafftechPhaseStatus')
    swarcoUTCTrafftechPlanCurrent = os.getenv('swarcoUTCTrafftechPlanCurrent')
    swarcoUTCTrafftechPlanSource = os.getenv('swarcoUTCTrafftechPlanSource')
    swarcoSoftIOStatus = os.getenv('swarcoSoftIOStatus')
    swarcoUTCDetectorQty = os.getenv('swarcoUTCDetectorQty')
    swarcoUTCSignalGroupState = os.getenv('swarcoUTCSignalGroupState')
    swarcoUTCSignalGroupOffsetTime = os.getenv('swarcoUTCSignalGroupOffsetTime')
    potokS_UTCCommandAllRed = os.getenv('potokS_UTCCommandAllRed')
    potokS_UTCSetGetLocal = os.getenv('potokS_UTCSetGetLocal')
    potokS_UTCprohibitionManualPanel = os.getenv('potokS_UTCprohibitionManualPanel')
    potokS_UTCCommandRestartProgramm = os.getenv('potokS_UTCCommandRestartProgramm')
    potokS_UTCStatusMode = os.getenv('potokS_UTCStatusMode')

    """" UG405 """
    # -- Control Bits --#
    utcControlLO = os.getenv('utcControlLO')
    utcControlFF = os.getenv('utcControlFF')
    utcControlTO = os.getenv('utcControlTO')
    utcControlFn = os.getenv('utcControlFn')
    # -- Reply Bits --#
    utcType2Reply = os.getenv('utcType2Reply')
    utcType2Version = os.getenv('utcType2Version')
    utcReplySiteID = os.getenv('utcReplySiteID')
    utcType2VendorID = os.getenv('utcType2VendorID')
    utcType2HardwareType = os.getenv('utcType2HardwareType')
    utcType2OperationModeTimeout = os.getenv('utcType2OperationModeTimeout')
    utcType2OperationMode = os.getenv('utcType2OperationMode')
    utcReplyGn = os.getenv('utcReplyGn')
    utcReplyFR = os.getenv('utcReplyFR')
    utcReplyDF = os.getenv('utcReplyDF')
    utcReplyMC = os.getenv('utcReplyMC')
    utcReplyCF = os.getenv('utcReplyCF')
    utcReplyVSn = os.getenv('utcReplyVSn')
    utcType2OutstationTime = os.getenv('utcType2OutstationTime')
    utcType2ScootDetectorCount = os.getenv('utcType2ScootDetectorCount')
    # -- Control Bits --#(Spec PotokP)
    potokP_utcControRestartProgramm = os.getenv('potokP_utcControRestartProgramm')
    # -- Reply Bits --#(Spec PotokP)
    potokP_utcReplyPlanStatus = os.getenv('potokP_utcReplyPlanStatus')
    potokP_utcReplyPlanSource = os.getenv('potokP_utcReplyPlanSource')
    potokP_utcReplyDarkStatus = os.getenv('potokP_utcReplyDarkStatus')
    potokP_utcReplyLocalAdaptiv = os.getenv('potokP_utcReplyLocalAdaptiv')
    potokP_utcReplyHardwareErr = os.getenv('potokP_utcReplyHardwareErr')
    potokP_utcReplySoftwareErr = os.getenv('potokP_utcReplySoftwareErr')
    potokP_utcReplyElectricalCircuitErr = os.getenv('potokP_utcReplyElectricalCircuitErr')


class BaseCommon:
    """
    Базовый класс для всех типов контроллеров и протоколов мониторинга/управления
    """

    statusMode = {
        '3': 'Сигналы выключены(ОС)',
        '4': 'Жёлтое мигание',
        '5': 'Заблокирован инспектором',
        '6': 'Кругом Красный',
        '8': 'Адаптивный',
        '10': 'Ручное управление',
        '11': 'Удалённое управление',
        '12': 'Фиксированный',
        '00': 'Ошибка электрической цепи',
        '14': 'Жёлтое мигание по расписанию',
        '--': 'Нет данных',
        'FT': 'Фиксированный',
        'VA': 'Адаптивный',
        'MAN': 'Ручное управление',
        'UTC': 'Удалённое управление',
        'CLF': 'Бесцентровая синхронизация',
        'ЛАМПЫ ВЫКЛ': 'Сигналы выключены(ОС)',
        'ЖЕЛТОЕ МИГАНИЕ': 'Жёлтое мигание',
        'КРУГОМ КРАСНЫЙ': 'Кругом Красный',
        'ЗАБЛОКИРОВАН ИНСПЕКТОРОМ': 'Заблокирован инспектором',
        'УПРАВЛЕНИЕ': 'Управление',
        'CONTROL': 'Управление'
    }

    type_request: EntityJsonResponce | None
    controller_type: str | None
    parse_varBinds: Callable
    get_current_mode: Callable

    def __init__(self, ip_adress, host_id=None):
        self.ip_adress = ip_adress
        self.host_id = host_id
        self.errorIndication = None
        self.varBinds = None
        self.req_data = {}
        self.get_entity = []
        self.set_entity = {}
        self.result_set_command = None
        self.responce_time = None

    @staticmethod
    def set_curr_datetime(sep: str = ':') -> str:
        """
        Возвращает текущую дату и время
        :param sep: разделитель между датой и временем
        :return: отформатированная строка с датой и временем
        """

        return datetime.today().strftime(f"%Y-%m-%d %H{sep}%M{sep}%S")

    @staticmethod
    def reverse_slashes(path: str) -> str:
        """
        Модифицирует path, разворачивая косую черту \\ на /
        :param path: строка с path, которую требуется модифицировать
        :return: модицицированная строка path
        """

        return path.replace('\\', '/')

    @staticmethod
    def save_json_to_file(json_data, file_name='controller_management.json', mode: str = 'w') -> None:
        """
        Формирует json и записывает в файл
        :param json_data: словарь, который будет записан как json
        :param file_name: путь к файлу
        :param mode: режим записи в файл
        :return:
        """

        with open(file_name, mode, encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
            f.write('\n\n')

    def set_controller_type(self) -> None:
        """
        Метод устанавливает в атрибут экземпляра тип контроллера
        """

        if isinstance(self, (SwarcoSTCIP, SwarcoSSHBase, SwarcoWebBase)):
            self.controller_type = AvailableControllers.SWARCO.value
        elif isinstance(self, PotokP):
            self.controller_type = AvailableControllers.POTOK_P.value
        elif isinstance(self, PotokS):
            self.controller_type = AvailableControllers.POTOK_S.value
        elif isinstance(self, (PeekUG405, PeekWeb)):
            self.controller_type = AvailableControllers.PEEK.value
        else:
            self.controller_type = None

    def put_to_get_entity(self, data: str | list) -> None:
        """
        Добавляет в json responce свойство 'get_entity'
        :param data: данные, которые будут добавлены в атрибут self.get_entity
        :return: None
        """

        if isinstance(data, str):
            self.get_entity.append(data)
        elif isinstance(data, list):
            self.get_entity += data

    def put_to_req_data(self, data: dict) -> None:
        """
        Добавляет в json responce свойство 'req_data'
        :param data: данные, которые будут добавлены в атрибут self.req_data
        :return: None
        """

        if isinstance(data, dict):
            self.req_data |= data

    def put_data_to_request_entity(self) -> None:
        """
        Добавляет в json responce свойство self.put_to_get_entity или  self.put_to_req_data
        :return: None
        """

        if self.get_entity and self.set_entity or not self.get_entity and not self.set_entity:
            raise ValueError

        if self.get_entity:
            self.req_data[EntityJsonResponce.REQUEST_ENTITY.value] = self.get_entity
        else:
            self.req_data[EntityJsonResponce.REQUEST_ENTITY.value] = self.set_entity

    def create_json(self, errorIndication: None | Exception | str, varBinds: list, **kwargs) -> dict:
        """"
        Метод формирует словарь вида json
        :arg errorIndication: None если не было ошибки при запросе иначе класс ошибки или str
        :param varBinds: список varBinds, полученный после запроса
        :arg kwargs: параметры, которые будут добавлены в словарь

        пример get_mode peek:
        {
            "protocol": "http",
            "type": "get",
            "request_time": "2024-11-22 13:27:10",
            "type_controller": "Peek",
            "host_id": 1,
            "request_errors": null,
            "request_entity": [
                "get_mode"
            ],
            "responce_entity": {
                "raw_data": {
                    "current_states": {
                        "basic": {
                            "current_plan": "001",
                            "current_parameter_plan": "001",
                            "current_time": "2024-11-22 13:26:43",
                            "current_errors": "ISWC",
                            "streams": 1,
                            "stream_info": {
                                "1": {
                                    "current_mode": "FT",
                                    "current_stage": "1",
                                    "current_state": "УПРАВЛЕНИЕ"
                                }
                            }
                        }
                    }
                }
            }
        }

        пример get_mode swarco:
        {
            "protocol": "http",
            "type": "get",
            "request_time": "2024-11-27 09:14:23",
            "type_controller": "Swarco",
            "host_id": 9,
            "request_errors": null,
            "request_entity": [
                "get_mode"
            ],
            "responce_entity": {
                "raw_data": {
                    "current_states": {
                        "basic": {
                            "current_mode": "LOCAL",
                            "current_stage": "S2/S3",
                            "current_stage_time": "4",
                            "current_cyc": "21",
                            "current_plan": "P1Ка",
                            "system_time": "27.11-09:14:23",
                            "current_state_buttons": "SIGNALS=ON | FIXED_CTRL=ON",
                            "web_content": [
                                "*** ITC-2 Linux  ***",
                                "13024 27.11-09:14:23",
                                "P1Ка      LOCAL   21",
                                "1-1 ВКЛ_ОК S2/S3 4  ",
                                "1 0 0 0 0 0 1 0",
                                "SIGNALS=ON | FIXED_CTRL=ON"
                            ]
                        }
                    }
                }
            }
        }
        пример get_mode поток:
        {
            "protocol": "snmp",
            "type": "get",
            "request_time": "2024-11-27 09:14:23",
            "type_controller": "Поток (P)",
            "host_id": 8,
            "request_errors": null,
            "request_entity": [
                "get_mode"
            ],
            "responce_entity": {
                "raw_data": {
                    "current_states": {
                        "basic": {
                            "current_mode": "Фиксированный",
                            "current_stage": "1",
                            "current_plan": "1"
                        }
                    }
                }
            }
        }

        пример set stage peek web:
        {
            "protocol": "http",
            "type": "set",
            "request_time": "2024-11-23 13:38:34",
            "type_controller": "Peek",
            "host_id": "1",
            "request_errors": null,
            "request_entity": {
                "set_stage": "5"
            },
            "responce_entity": {
                "raw_data": {
                    "current_states": {
                        "inputs": [
                            "MPP_MAN: ВКЛ",
                            "MPP_FL: -",
                            "MPP_OFF: -",
                            "MPP_PH1: ВЫКЛ",
                            "MPP_PH2: ВЫКЛ",
                            "MPP_PH3: ВЫКЛ",
                            "MPP_PH4: ВЫКЛ",
                            "MPP_PH5: ВКЛ",
                            "MPP_PH6: ВЫКЛ",
                            "MPP_PH7: ВЫКЛ",
                            "MPP_PH8: ВЫКЛ"
                        ],
                        "basic": {
                            "current_plan": "001",
                            "current_parameter_plan": "001",
                            "current_time": "2024-11-23 13:38:08",
                            "current_errors": "ISWC",
                            "streams": 1,
                            "stream_info": {
                                "1": {
                                    "current_mode": "FT",
                                    "current_stage": "4",
                                    "current_state": "УПРАВЛЕНИЕ"
                                }
                            }
                        }
                    },
                    "sent_commands": [
                        {
                            "MPP_PH1": "ВЫКЛ"
                        },
                        {
                            "MPP_PH2": "ВЫКЛ"
                        },
                        {
                            "MPP_PH3": "ВЫКЛ"
                        },
                        {
                            "MPP_PH4": "ВЫКЛ"
                        },
                        {
                            "MPP_PH5": "ВКЛ"
                        },
                        {
                            "MPP_PH6": "ВЫКЛ"
                        },
                        {
                            "MPP_PH7": "ВЫКЛ"
                        },
                        {
                            "MPP_PH8": "ВЫКЛ"
                        },
                        {
                            "MPP_MAN": "ВКЛ"
                        }
                    ]
                },
                "result": "request sent successfully",
                "success": true,
                "responce_time": null
            }
        }

        """

        self.req_data |= {k: v for k, v in zip(JsonBody.BASE_JSON_BODY.value, (self.controller_type, self.host_id))}
        logger.debug('self.req_data %s' % self.req_data)
        errorIndication = errorIndication.__str__() if errorIndication is not None else errorIndication
        self.req_data[EntityJsonResponce.REQUEST_ERRORS.value] = errorIndication
        self.put_data_to_request_entity()

        if errorIndication:
            if kwargs:
                self.req_data |= {k: v for k, v in kwargs.items()}
            return self.req_data

        if isinstance(self, PeekWebContent):
            varBinds = self.varBinds_to_dict(varBinds)

        if self.get_entity:
            self.create_struct_responce_get(varBinds)
        elif self.set_entity:
            self.create_struct_responce_set(varBinds)
        else:
            raise ValueError
        logger.debug(self.req_data)
        if kwargs:
            self.req_data |= {k: v for k, v in kwargs.items()}
        # self.save_json_to_file(self.req_data, 'controller_management_responce.json')
        return self.req_data

    def create_struct_responce_set(self, varBinds: list | str | dict) -> None:
        """
        Метод формирует структуру json responce для запроса типа set атрибута self.req_data
        :param varBinds: различные данные, характерные для протокола получения и типа контроллера данные.
                         Например: отправленные команды, статус состояния после отправки команды и т.д.
        :return: None
        """

        curr_states = {}
        sent_commands = []
        raw_data = {
            EntityJsonResponce.CURRENT_STATES.value: curr_states,
            EntityJsonResponce.SENT_COMMANDS.value: sent_commands,
        }
        self.req_data[EntityJsonResponce.RESPONCE_ENTITY.value] = {
            EntityJsonResponce.DATA_RESPONCE.value: raw_data,
            EntityJsonResponce.RESULT.value: EntityJsonResponce.REQ_SENT_SUCCESSFULLY.value,
            EntityJsonResponce.SUCCESS.value: True,
            EntityJsonResponce.RESPONCE_TIME.value: self.responce_time
        }
        parsed_varBinds = self.parse_varBinds(varBinds)
        logger.debug(parsed_varBinds)
        for i, data in enumerate(parsed_varBinds):
            if i == 0:
                raw_data[EntityJsonResponce.SENT_COMMANDS.value] = data
                continue
            logger.debug(data)
            for nested_data in data:
                if i == 1:
                    curr_states |= nested_data
        # self.save_json_to_file(self.req_data, 'controller_management_responce.json')
        logger.debug(self.req_data)

    def create_struct_responce_get(self, varBinds):
        """
        Метод формирует структуру json responce для запроса типа get атрибута self.req_data
        :param varBinds: различные данные, характерные для протокола получения и типа контроллера данные.
                         Например: отправленные команды, статус состояния после отправки команды и т.д.
        :return: None
        """

        curr_states = {}
        raw_data = {
            EntityJsonResponce.CURRENT_STATES.value: curr_states
        }
        self.req_data[EntityJsonResponce.RESPONCE_ENTITY.value] = {
            EntityJsonResponce.DATA_RESPONCE.value: raw_data
        }

        if EntityJsonResponce.GET_MODE.value in self.req_data.get(EntityJsonResponce.REQUEST_ENTITY.value):
            flag_get_mode = True
        else:
            flag_get_mode = False

        if flag_get_mode:
            varBinds, basic_mode = self.get_current_mode(varBinds)
            logger.debug(basic_mode)
            curr_states |= basic_mode
            logger.debug(curr_states)

        if varBinds:
            data_varBinds = self.parse_varBinds(varBinds)
            curr_states |= data_varBinds
        # self.save_json_to_file(self.req_data, 'controller_management_responce.json')

    def has_error_in_taskgroup(self, result: list[asyncio.Task]) -> None | str:
        """
        Метод проверяет есть ли ошибки после запроса
        :param result: результат завершенных задач Taskgroup()
        :return: None если нет ошибки, иначе текст ошибки
        """

        error_indication = None
        for r in result:
            try:
                r.result()
            except asyncio.TimeoutError:
                error_indication = EntityJsonResponce.TIMEOUT_ERROR_WEB_REQUEST_MSG.value
            except aiohttp.client_exceptions.ClientConnectorCertificateError:
                error_indication = EntityJsonResponce.TYPE_CONTROLLER_ERROR_MSG.value
            except aiohttp.client_exceptions.ClientConnectorError:
                error_indication = EntityJsonResponce.NETWORK_CONNECTION_ERROR.value
            except TypeError:
                error_indication = EntityJsonResponce.TYPE_CONTROLLER_ERROR_MSG.value
            finally:
                return error_indication


class BaseSNMP(BaseCommon):
    """
    Базовый класс для snmp запросов по всем протоколам: set и get запросы
    """
    user_oids: list | tuple | set
    scn: str
    get_state_oids: set
    matching_types_set_req: dict
    community_read: str
    community_write: str

    def __init__(self, ip_adress, host_id=None):
        super().__init__(ip_adress, host_id)

    async def get_request_base(
            self,
            ip_adress: str,
            community: str,
            oids: list[str],
            json_responce: bool = False,
            timeout: float = 0,
            retries: int = 1
    ) -> tuple:
        """
        Метод get запросов по snmp
        :arg ip_adress: ip хоста
        :arg community: коммьюнити хоста
        :arg oids: список oids, которые будут отправлены в get запросе
        :arg timeout: таймаут запроса, в секундах
        :arg retries: количество попыток запроса
        :return: tuple вида:
                 index[0] -> если есть ошибка в snmp запросе, то текст ошибки, иначе None
                 index[1] -> ответные данные. список вида [(oid, payload), (oid, payload)...]
                 index[2] -> self, ссылка на объект

        Examples
        --------
        ip_adress = '192.168.0.1'\n
        community = 'community'\n
        oids = [Oids.swarcoUTCTrafftechPhaseStatus.value,
               Oids.swarcoUTCTrafftechPlanStatus.value]


        asyncio.run(set_request(ip_adress, community, oids))
        ******************************
        """

        if self.get_entity:
            self.put_to_req_data({
                EntityJsonResponce.PROTOCOL.value: EntityJsonResponce.SNMP.value,
                EntityJsonResponce.TYPE.value: EntityJsonResponce.GET.value,
                EntityJsonResponce.REQUEST_TIME.value: self.set_curr_datetime()
            })

        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip_adress, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )

        # logging.debug(
        #     f'errorIndication: {errorIndication.__str__()}\n'
        #     f'errorStatus: {errorStatus}\n'
        #     f'errorIndex: {errorIndex}\n'
        #     f'varBinds: {varBinds}\n'
        # )
        # print(f'errorIndication .__str__: {errorIndication.__str__()}')
        # print(f'errorIndication: {errorIndication}')
        # print(f'errorIndication type : {type(errorIndication)}')
        # print(f'errorStatus: {errorStatus}')
        # print(f'errorIndex: {errorIndex}')
        # print(f'varBinds: {varBinds}')
        self.errorIndication, self.varBinds = errorIndication, varBinds
        return errorIndication, varBinds, self

    async def getNext_request_base(
            self,
            ip_adress: str,
            community: str,
            oids: list[str],
            timeout: float = 0,
            retries: int = 0
    ):

        errorIndication, errorStatus, errorIndex, varBinds = await nextCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip_adress, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return errorIndication, varBinds, self

    async def set_request_base(
            self,
            ip_adress: str,
            community: str,
            oids: list[tuple[str, Any]] | dict[str, Any],
            timeout: float = 0,
            retries: int = 0
    ) -> tuple:
        """
        Метод set запросов по snmp
        :param ip_adress: ip хоста
        :param community: коммьюнити хоста
        :param oids: list или dict из оидов и значений, которые будут установлены
        :param timeout: таймаут запроса, в секундах
        :param retries: количество попыток запроса
        :return: tuple вида:
                 index[0] -> если есть ошибка в snmp запросе, то текст ошибки, иначе None
                 index[1] -> ответные данные. список вида [(oid, payload), (oid, payload)...]
                 index[2] -> self, ссылка на объект

        Examples
        --------
        Если переданные oids -> list[tuple]:

        ip_adress = '192.168.0.1'\n
        community = 'community'\n
        oids = [(Oids.swarcoUTCTrafftechPhaseCommand.value, Unsigned32('2')),
               (Oids.swarcoUTCTrafftechPlanCommand.value, Unsigned32('2')) ]

        asyncio.run(set_request(ip_adress, community, oids))
        ******************************

        Если переданные oids -> dict:

        ip_adress = '192.168.0.1'\n
        community = 'community'\n
        oids = {Oids.swarcoUTCTrafftechPhaseCommand.value: Unsigned32('2'),
                Oids.swarcoUTCTrafftechPlanCommand.value: Unsigned32('2')}


        asyncio.run(set_request(ip_adress, community, oids))
        ******************************
        """

        self.put_to_req_data({
            EntityJsonResponce.PROTOCOL.value: EntityJsonResponce.SNMP.value,
            EntityJsonResponce.TYPE.value: EntityJsonResponce.SET.value,
            EntityJsonResponce.REQUEST_TIME.value: self.set_curr_datetime(),
        })
        oids = list(oids.items() if type(oids) is dict else oids)
        errorIndication, errorStatus, errorIndex, varBinds = await setCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip_adress, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid), val) for oid, val in oids]
        )
        logging.debug(
            f'\nerrorIndication: {errorIndication.__str__()}\n'
            f'errorStatus: {errorStatus}\n'
            f'errorIndex: {errorIndex}\n'
            f'varBinds: {varBinds}\n'
        )
        self.errorIndication, self.varBinds = errorIndication, varBinds
        self.responce_time = self.set_curr_datetime()
        return errorIndication, varBinds, self

    def _create_data_for_get_req(self, oids: list[str], get_mode: bool) -> list:
        """
        Метод формирует коллекцию оидов для отправки в соответствии с переданными параметрами
        :arg oids: коллекция оидов для  get запроса от пользователя
        :arg get_mode: флаг, говорящий о необходимости получения базового состояния ДК:
                       режим, фаза, план
        :return processed_oids: финальная коллекция оидов, которые будут отправлены хосту в get запросе(snmp)
        """

        if get_mode:
            if isinstance(self, (PotokP, PeekUG405)):
                processed_oids = [self.add_scn_to_oid(self.check_type_oid(oid))
                                  for oid in itertools.chain(self.get_state_oids, oids)]
            else:
                processed_oids = [self.check_type_oid(oid) for oid in itertools.chain(self.get_state_oids, oids)]
        else:
            if isinstance(self, (PotokP, PeekUG405)):
                processed_oids = [self.add_scn_to_oid(self.check_type_oid(oid)) for oid in oids]
            else:
                processed_oids = [self.check_type_oid(oid) for oid in oids]
        return processed_oids

    def _create_data_for_set_req(
            self, oids: list[str, str] | dict[str, str], unique_oids: bool = False
    ) -> list | set:
        """
        Метод формирует оиды необходимые для запроса.
        :param oids: оиды и значения, которые необходимо установить на ДК
        :param unique_oids: если требуется, чтобы все устанавливаемые оиды были уникальны
        :return: оиды для отправки. Примеры возвращаемой коллекции:

        """

        processed_oids = []

        oids = list(oids.items()) if type(oids) == dict else oids
        for oid, val in oids:
            oid = self.check_type_oid(oid)
            if isinstance(self, (PotokP, PeekUG405)):
                oid = self.add_scn_to_oid(oid)
            processed_oids.append((oid, self.matching_types_set_req.get(oid)(val)))

        return processed_oids if not unique_oids else set(processed_oids)

    async def get_request(self, oids: list[str] = None, get_mode: bool = False) -> tuple:
        """
        Отправляет get запрос по протоколу snmp
        :param oids: список из oid`s, которые будут отправлены хосту
        :param get_mode: требуется ли запрос на получения состояния дк(фаза, план, режим управления и т.д.)
        :return: кортеж вида (Ошибки, контент запроса, self)

        Examples
        --------
        oids = [Oids.swarcoUTCTrafftechPhaseStatus.value,
               Oids.swarcoUTCTrafftechPlanStatus.value]

        asyncio.run(set_request(oids))
        ******************************

        """

        logger.debug(oids)
        if get_mode:
            self.put_to_get_entity(EntityJsonResponce.GET_MODE.value)

        if not oids and not get_mode:
            self.errorIndication, self.varBinds = EntityJsonResponce.NO_DATA_FOR_REQ.value, []
            return None, [], self

        oids = [self.check_type_oid(oid) for oid in oids] if oids else []
        all_oids = {o.value for o in Oids}
        self.put_to_get_entity([Oids(oid).name if oid in all_oids else oid for oid in oids])

        if isinstance(self, (PotokP, PeekUG405)):
            if not self.scn:
                self.scn = await self.get_scn()

        processed_oids = self._create_data_for_get_req(oids, get_mode)
        logger.debug(processed_oids)

        return await self.get_request_base(
            ip_adress=self.ip_adress,
            community=self.community_read,
            oids=processed_oids
        )

    async def set_request(self, oids: list[tuple[str, Any]] | dict[str, Any]) -> tuple:
        """"
        Отправляет set запрос по протоколу snmp
        :arg oids: oid`s и значения, которые будут отправлены хосту. Могут быть списком кортежей либо словарём:
                   Пример, если list: [(oid, val), (oid, val)...]
                   Пример, если dict: {oid: val, oid: val...}
        :return: кортеж вида (Ошибки, контент запроса, self)

        Examples
        --------
        Если переданные oids -> list[tuple]:

        oids = [(Oids.swarcoUTCTrafftechPhaseCommand.value, Unsigned32('2')),
               (Oids.swarcoUTCTrafftechPlanCommand.value, Unsigned32('2')) ]


        asyncio.run(set_request(oids))
        ******************************

        Если переданные oids -> dict:

        oids = {Oids.swarcoUTCTrafftechPhaseCommand.value: Unsigned32('2'),
                Oids.swarcoUTCTrafftechPlanCommand.value: Unsigned32('2')}


        asyncio.run(set_request(oids))
        ******************************
        """

        if not oids:
            self.errorIndication, self.varBinds = EntityJsonResponce.NO_DATA_FOR_REQ.value, []
            return None, [], self

        if isinstance(self, (PotokP, PeekUG405)):
            if not self.scn:
                self.scn = await self.get_scn()
        all_oids = {o.value for o in Oids}
        self.set_entity += [Oids(oid).name if oid in all_oids else oid for oid in oids]
        processed_oids = self._create_data_for_set_req(oids)

        return await self.set_request_base(
            ip_adress=self.ip_adress,
            community=self.community_write,
            oids=processed_oids
        )

    @staticmethod
    def check_type_oid(oid: Oids | str) -> str:
        """
        Метод проверяет корректность типа переданного оида
        :param oid: Проверяемый оид
        :return: оид типа str
        """

        if type(oid) is not str:
            if isinstance(oid, Oids):
                oid = Oids(oid).value
            else:
                raise ValueError(f'Оид должен быть строкой или или атрибутом класса Oids , type oid: '
                                 f'{type(oid)}, val oid: {oid}')

        return oid

    def parse_varBinds(self, varBinds: list) -> dict | tuple:
        """
        Обрабатывает и формирует данные, полученные после get/set запроса
        :param varBinds: данные, после get/set запроса
        :return: обработанные данные, необходимые для функции create_json класса BaseCommon
        """

        oids = []
        for oid, val in varBinds:
            oid, val = oid.__str__(), val.prettyPrint()
            if isinstance(self, (PotokP, PeekUG405)):
                if oid.endswith(self.scn):
                    oid = oid.replace(self.scn, '')
            oid_name, oid_val = Oids(oid).name, Oids(oid).value
            oid = f'{oid_name}[{oid_val}]'
            if (Oids.swarcoUTCTrafftechPhaseStatus.name in oid_name or Oids.swarcoUTCTrafftechPhaseCommand.name
                    in oid_name or Oids.utcReplyGn.name in oid_name):
                num_stage = self.convert_val_to_num_stage_get_req(val)
                val = f'num_stage[{num_stage}], val_stage[{val}]'

            oids.append({oid: val})

        if self.get_entity:
            return {'oids': oids}
        elif self.set_entity:
            return oids, []


class BaseSTCIP(BaseSNMP):
    """
    Базовый класс для SNMP запросов по протоколу STCIP
    """

    convert_val_to_num_stage_set_req: Callable
    converted_values_all_red: dict
    community_write = os.getenv('communitySTCIP_w')
    community_read = os.getenv('communitySTCIP_r')

    converted_values_flash_dark = {
        '1': '2', 'true': '2', 'on': '2', 'вкл': '2', '2': '2',
        '0': '0', 'false': '0', 'off': '0', 'выкл': '0',
    }
    matching_types_set_req = {
        Oids.swarcoUTCTrafftechPhaseCommand.value: Unsigned32,
        Oids.swarcoUTCTrafftechPlanCommand.value: Unsigned32
    }

    """ GET REQUEST """

    """ SET REQUEST """

    async def set_stage(self, value='0', timeout=1, retries=2) -> tuple:
        """"
        Устанавливает  фазу по протоколу STCIP.
        :param value:  Номер фазы в десятичном виде
        :param retries:
        :param timeout:
        :return: ErrorIndication, varBinds
        """

        self.set_entity[inspect.stack()[0][3]] = value
        converted_val = self.convert_val_to_num_stage_set_req(value.lower())
        oids = [
            (Oids.swarcoUTCTrafftechPhaseCommand.value, Unsigned32(converted_val)),
        ]
        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)

    async def set_allred(self, value='0', timeout=1, retries=2) -> tuple:
        """"
        Устанавливает или сбрасывает режим КК по протоколу STCIP.
        :param retries:
        :param timeout:
        :param value: значение. см ассоциации в self.converted_values_all_red
        :return: ErrorIndication, varBinds
        """

        self.set_entity[inspect.stack()[0][3]] = value
        if isinstance(self, SwarcoSTCIP):
            oid = Oids.swarcoUTCTrafftechPlanCommand.value
        else:
            oid = Oids.potokS_UTCCommandAllRed.value
        value = self.converted_values_all_red.get(value.lower())
        oids = [(oid, Unsigned32(value))]

        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)

    async def set_flash(self, value='0', timeout=1, retries=2) -> tuple:
        """"
        Устанавливает ЖМ(или сбрасывает ранее установленный в swarcoUTCCommandFlash) по протоколу STCIP.
        :param retries:
        :param timeout:
        :param value: 2 -> устанавливает ОС, 0 -> сбрасывает ранее установленный ЖМ
        """

        self.set_entity[inspect.stack()[0][3]] = value
        value = self.converted_values_flash_dark.get(value.lower())
        oids = [(Oids.swarcoUTCCommandFlash.value, Integer32(value))]

        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)

    async def set_dark(self, value='0', timeout=1, retries=2) -> tuple:
        """"
        Устанавливает ОС(или сбрасывает ранее установленный в swarcoUTCCommandDark) по протоколу STCIP.
        :param retries: количество попыток отправки запроса
        :param timeout: таймаут оправки snmp запроса
        :param value: 2 -> устанавливает ОС, 0 -> сбрасывает ранее установленный ОС
        :return: Возвращает значение установленного swarcoUTCCommandDark
        """

        self.set_entity[inspect.stack()[0][3]] = value
        value = self.converted_values_flash_dark.get(value.lower())
        oids = [(Oids.swarcoUTCCommandDark.value, Integer32(value))]

        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)


class BaseUG405(BaseSNMP):
    """
    Базовый класс для SNMP запросов по протоколу UG405
    """

    community_read = os.getenv('communityUG405_r')
    community_write = os.getenv('communityUG405_w')

    scn_required_oids = {
        Oids.utcReplyGn.value, Oids.utcReplyFR.value, Oids.utcReplyDF.value, Oids.utcControlTO.value,
        Oids.utcControlFn.value, Oids.potokP_utcReplyPlanStatus.value, Oids.potokP_utcReplyPlanSource.value,
        Oids.potokP_utcReplyPlanSource.value, Oids.potokP_utcReplyDarkStatus.value,
        Oids.potokP_utcReplyLocalAdaptiv.value, Oids.potokP_utcReplyHardwareErr.value,
        Oids.potokP_utcReplySoftwareErr.value, Oids.potokP_utcReplyElectricalCircuitErr.value,
        Oids.utcReplyMC.value, Oids.utcReplyCF.value, Oids.utcReplyVSn.value
    }

    def __init__(self, ip_adress, scn=None, host_id=None):
        super().__init__(ip_adress, host_id)
        self.ip_adress = ip_adress
        self.scn = self.convert_scn(scn) if scn else scn
        self.host_id = host_id

    @staticmethod
    def convert_scn(scn: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """

        return f'.1.{str(len(scn))}.{".".join([str(ord(c)) for c in scn])}'

    def add_scn_to_oid(self, oids: set[str] | tuple[str] | list[str] | str, scn: str = None) -> str | list:
        """
        Метод добавляет scn к оиду.
        :param oids: один оид в виде строки или коллекция оидов, где каждый элемент коллекции - оид типа str
        :param scn: если None, то взять scn из self
        :return: если на вход дан один оид(str) то возвращаем также один оид + scn в виде строки.
                 если на вход дана коллекция, возвращаем коллекцию оидов с scn
        """

        scn = self.scn if scn is None else scn
        if isinstance(oids, str):
            if oids in self.scn_required_oids:
                return oids + scn
            return oids

        new_oids = []
        for oid in oids:
            oid = self.check_type_oid(oid)
            if oid in self.scn_required_oids:
                new_oids.append(oid + scn)
            else:
                new_oids.append(oid)
        return new_oids

    def remove_scn_from_oid(self, oid: str) -> str:
        """
        Метод удаляет scn у оида.
        :arg oid: оид, который необходимо проверить на наличие в нём scn
        :return oid: возвращает оид без scn
        """

        return oid.replace(self.scn, '') if self.scn in oid else oid

    @staticmethod
    def convert_val_to_num_stage_set_req(val: str) -> int | None:
        """
        Конвертирует десятичное значение фазы в отображение hex, для snmp set request
        :param val: значение фазы в десятичном виде
        :return: значение в виде hex отображения для отправки в oid фазы
        """

        stg_mask = ['01', '02', '04', '08', '10', '20', '40', '80']
        values = {str(k): v for k, v in enumerate((f'{i}{j * "00"}' for j in range(8) for i in stg_mask), 1)}
        return values.get(val)

    @staticmethod
    def convert_val_to_num_stage_get_req(val: str) -> int:
        """
        Конвертирует значение, полученное из oid фазы в номер фазы десятичного представления
        :param val: значение, необходимое отобразить в десятичном виде
        :return: значение(номер) фазы в десятичном виде
        """

        try:
            if val not in (' ', '@'):
                return int(math.log2(int(val, 16))) + 1
            elif val == ' ':
                return 6
            elif val == '@':
                return 7
        except ValueError:
            logger.warning(f'Значение val: {val}')

    """ GET REQUEST """

    async def get_scn(self) -> str:
        """
        Получает scn из snmp запроса
        :return: scn хоста
        """

        if isinstance(self, PeekUG405):
            errorIndication, varBinds, _ = await self.getNext_request_base(
                self.ip_adress, self.community_read,  [Oids.utcType2Reply.value]
            )
            if errorIndication is None and varBinds:
                oid = varBinds[0][0][0].__str__()
                replace_fragment = Oids.utcReplyGn.value
                if replace_fragment in oid:
                    return oid.replace(replace_fragment, "")
            return ''

        elif isinstance(self, PotokP):
            logging.debug(f'get_scn: {self}')
            errorIndication, varBinds, _ = await self.get_request_base(
                self.ip_adress, self.community_read, [Oids.utcReplySiteID.value]
            )
            if errorIndication is None and varBinds:
                return self.convert_scn(varBinds[0][1].prettyPrint())
            return ''
        else:
            return ''

    async def get_operation_mode(self, timeout=0, retries=0) -> str:
        """
        Получает значение oid utcType2OperationMode
        :param timeout: таймаут snmp запроса
        :param retries: количество попыток запроса
        :return: значение в oid utcType2OperationMode
        """

        err, varBinds, _ = await self.get_request_base(
            self.ip_adress, self.community_write,
            oids=[Oids.utcType2OperationMode.value],
            timeout=timeout, retries=retries
        )
        _, curr_operation_mode = varBinds[0]

        return curr_operation_mode.prettyPrint()

    """ archive methods(not usage) """

    """ SET REQUEST """

    async def set_operation_mode(self, val: str | int, timeout=0, retries=0):
        """
        Устанавливает значение в oid utcType2OperationMode
        :param val: Значение, которое будет установлено в utcType2OperationMode
        :param timeout: таймаут запроса snmp
        :param retries: количество попыток запроса
        :return: кортеж вида (Ошибки, контент запроса, self)
        """

        return await self.set_request_base(
            self.ip_adress, self.community_write,
            oids=[(Oids.utcType2OperationMode.value, Integer32(val),)],
            timeout=timeout, retries=retries
        )


class SwarcoSTCIP(BaseSTCIP):
    """
    Класс интерфейс взаимодействия с ДК Swarco
    """

    converted_values_all_red = {
        '1': '119', 'true': '119', 'on': '119', 'вкл': '119', '2': '119', '119': '119',
        '0': '100', 'false': '100', 'off': '100', 'выкл': '100',
    }

    get_state_oids = {
        Oids.swarcoUTCStatusEquipment.value,
        Oids.swarcoUTCTrafftechPhaseStatus.value,
        Oids.swarcoUTCTrafftechPlanCurrent.value,
        Oids.swarcoUTCDetectorQty.value,
        Oids.swarcoSoftIOStatus.value,
    }

    def __init__(self, ip_adress, host_id=None):
        super().__init__(ip_adress, host_id)
        self.set_controller_type()
        # self._get_current_state = False

    @staticmethod
    def convert_val_to_num_stage_get_req(val: str) -> int | None:
        """
        Конвертирует значение из oid фазы в номер фазы из get заспроа
        :param val: значение, которое будет сконвертировано в десятичный номер фазы.
        :return: номер фазы в десятичном представлении
        """

        values = {'2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0}
        return values.get(val)

    @staticmethod
    def convert_val_to_num_stage_set_req(val: str) -> int | None:
        """
        Конвертирует номер фазы в значение для установки в oid фазы
        :param val: номер фазы, который будет сконвертирован в соответствующее значение
        :return: Значение фазы, которое будет установлено.
        """

        values = {'1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 1, 'ЛОКАЛ': 0, '0': 0}
        return values.get(val)

    """ GET REQUEST """

    def _mode_define(self, equipment_status: str, plan: str, softstat180_181: str, num_logics: str) -> str:
        """ Определяет текщий ружим ДК.
        :arg equipment_status (str): Текущий режим работы контроллера:
                                     workingProperly(1),
                                     powerUp(2),
                                     dark(3),
                                     flash(4),
                                     partialFlash(5),
                                     allRed(6)

        :arg plan (str): Текущий номер плана
        :arg softstat180_181 (str): Текущее состояние входов 180 и 181
        :arg num_logics (str): Количество детекторных логик

        :return str: Возращает текущий режим ДК(Фикс/Адаптива/КУ и т.д)
        """

        if equipment_status != '1':
            val_mode = equipment_status
        elif plan == '16':
            val_mode = '11'
        elif plan == '15':
            val_mode = '10'
        elif softstat180_181 is None or '1' in softstat180_181 or num_logics == '0':
            val_mode = '12'
        elif softstat180_181 == '00' and num_logics.isdigit() and int(num_logics) > 0:
            val_mode = '8'
        else:
            val_mode = '--'

        return self.statusMode.get(val_mode)

    def get_current_mode(self, varBinds: list) -> tuple:
        """
        Получает текующий режим на основе varBinds
        :param varBinds: varBinds[oid, val] после snmp запроса
        :return: new_varBins: оставшиеся необработанные значения oids после определения текущего режима ДК
                 текущий режим (словарь json-responce)
        """

        equipment_status = plan = softstat180_181 = num_logics = stage = None
        new_varBins = []
        user_oids = self.req_data.get(EntityJsonResponce.REQUEST_ENTITY.value)
        logger.debug(user_oids)
        for data in varBinds:
            oid, val = data[0].__str__(), data[1].prettyPrint()

            if oid in self.get_state_oids:
                if oid == Oids.swarcoUTCStatusEquipment.value:
                    equipment_status = val
                elif oid == Oids.swarcoUTCTrafftechPhaseStatus.value:
                    stage = self.convert_val_to_num_stage_get_req(val)
                elif oid == Oids.swarcoUTCTrafftechPlanCurrent.value:
                    plan = val
                elif oid == Oids.swarcoUTCDetectorQty.value:
                    num_logics = val
                elif oid == Oids.swarcoSoftIOStatus.value:
                    softstat180_181 = val[179:181] if len(val) > 180 else None
                if user_oids is not None and Oids(oid).name in user_oids:
                    logger.debug(user_oids)
                    new_varBins.append(data)
            else:
                new_varBins.append(data)
        mode = self._mode_define(equipment_status, plan, softstat180_181, num_logics)
        basic_curr_state = {EntityJsonResponce.BASIC_STATE.value: {
            EntityJsonResponce.CURRENT_MODE.value: mode,
            EntityJsonResponce.CURRENT_STAGE.value: str(stage),
            EntityJsonResponce.CURRENT_PLAN.value: plan,
        }
        }
        return new_varBins, basic_curr_state

    """ SET REQUEST """


class PotokS(BaseSTCIP):
    """
    Класс интерфейс взаимодействия с ДК Swarco
    """

    converted_values_all_red = {
        '1': '2', 'true': '2', 'on': '2', 'вкл': '2',
        '0': '0', 'false': '0', 'off': '0', 'выкл': '0',
    }

    get_state_oids = {
        Oids.swarcoUTCStatusEquipment.value,
        Oids.swarcoUTCTrafftechPhaseStatus.value,
        Oids.swarcoUTCTrafftechPlanCurrent.value,
        Oids.potokS_UTCStatusMode.value,
    }

    def __init__(self, ip_adress, host_id=None):
        super().__init__(ip_adress, host_id)
        self.set_controller_type()

    """ GET REQUEST """

    @staticmethod
    def convert_val_to_num_stage_get_req(val: str) -> int | None:
        """
        Конвертирует значение из oid фазы в номер фазы из get заспроа
        :param val: значение, которое будет сконвертировано в десятичный номер фазы.
        :return: номер фазы в десятичном представлении
        """

        values = {
            str(k) if k < 66 else str(0): v if v < 65 else 0 for k, v in zip(range(2, 67), range(1, 66))
        }
        return values.get(val)

    @staticmethod
    def convert_val_to_num_stage_set_req(val: str) -> int | None:
        """
        Конвертирует номер фазы в значение для установки в oid фазы
        :param val: номер фазы, который будет сконвертирован в соответствующее значение
        :return: Значение фазы, которое будет установлено.
        """

        values = {str(k): str(v) if k > 0 else '0' for k, v in zip(range(65), range(1, 66))}
        return values.get(val)

    def _mode_define(self, equipment_status: str, plan: str, status_mode: str) -> str:
        """
        Определяет текщий ружим ДК.
        :arg equipment_status (str): Текущий режим работы контроллера:
                                     workingProperly(1),
                                     powerUp(2),
                                     dark(3),
                                     flash(4),
                                     partialFlash(5),
                                     allRed(6)

        :arg plan (str): Текущий номер плана
        :arg softstat180_181 (str): Текущее состояние входов 180 и 181
        :arg num_logics (str): Количество детекторных логик

        :return str: Возращает текущий режим ДК(Фикс/Адаптива/КУ и т.д)
        """

        if equipment_status != '1':
            val_mode = equipment_status
        elif status_mode == '11' and plan == '16':
            val_mode = status_mode
        elif status_mode != '11' and status_mode in ('8', '10', '12'):
            val_mode = status_mode
        else:
            val_mode = '--'
        return self.statusMode.get(val_mode)

    def get_current_mode(self, varBinds: list) -> tuple:
        """
        Получает текующий режим на основе varBinds
        :param varBinds: varBinds[oid, val] после snmp запроса
        :return: new_varBins: оставшиеся необработанные значения oids после определения текущего режима ДК
                 текущий режим (словарь json-responce)
        """

        equipment_status = plan = status_mode = stage = None
        user_oids = self.req_data.get(EntityJsonResponce.REQUEST_ENTITY.value)
        new_varBins = []
        for data in varBinds:
            oid, val = data[0].__str__(), data[1].prettyPrint()
            if oid in self.get_state_oids:
                if oid == Oids.swarcoUTCStatusEquipment.value:
                    equipment_status = val
                elif oid == Oids.swarcoUTCTrafftechPhaseStatus.value:
                    stage = self.convert_val_to_num_stage_get_req(val)
                elif oid == Oids.swarcoUTCTrafftechPlanCurrent.value:
                    plan = val
                elif oid == Oids.potokS_UTCStatusMode.value:
                    status_mode = val
                if user_oids is not None and Oids(oid).name in user_oids:
                    logger.debug(user_oids)
                    new_varBins.append(data)
            else:
                new_varBins.append(data)
        mode = self._mode_define(equipment_status, plan, status_mode)
        basic_curr_state = {EntityJsonResponce.BASIC_STATE.value: {
            EntityJsonResponce.CURRENT_MODE.value: mode,
            EntityJsonResponce.CURRENT_STAGE.value: str(stage),
            EntityJsonResponce.CURRENT_PLAN.value: plan,
        }
        }
        return new_varBins, basic_curr_state

    """ SET REQUEST """

    async def set_restart_program(self, value='1', timeout=1, retries=2) -> tuple:
        """"
        Перезапускает рабочую программу
        :param value: 1 -> команда на перезапуск рабочей программы
        :param retries: количество попыток запроса
        :param timeout: таймаут snmp запроса
        """

        oids = [(Oids.potokS_UTCCommandRestartProgramm.value, Unsigned32(value))]
        return await self.set_request_base(
            self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries
        )

    async def set_potokUTCSetGetLocal(self, value='1', timeout=1, retries=2) -> tuple:
        """"
        Перезапускает рабочую программу
        :param retries:
        :param timeout:
        :param value: 1 -> команда на перезапуск рабочей программы
        """

        oids = [(Oids.potokS_UTCSetGetLocal.value, Unsigned32(value))]
        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)

    async def set_potokUTCprohibitionManualPanel(self, value='1', timeout=1, retries=2) -> tuple:
        """"
        Перезапускает рабочую программу
        :param retries:
        :param timeout:
        :param value: 1 -> команда на перезапуск рабочей программы
        """

        oids = [(Oids.potokS_UTCprohibitionManualPanel.value, Unsigned32(value))]
        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)


class PotokP(BaseUG405):

    get_state_oids = {
        Oids.utcType2OperationMode.value,
        Oids.utcReplyCF.value,
        Oids.utcReplyFR.value,
        Oids.potokP_utcReplyDarkStatus.value,
        Oids.utcReplyMC.value,
        Oids.potokP_utcReplyPlanStatus.value,
        Oids.utcReplyGn.value,
        Oids.utcReplyDF.value,
        Oids.potokP_utcReplyLocalAdaptiv.value,
    }

    def __init__(self, ip_adress, host_id=None, scn=None):
        super().__init__(ip_adress, scn, host_id)
        self.set_controller_type()

        print(f'scn: {scn}')


    @staticmethod
    def convert_val_to_num_stage_set_req(val: str) -> int | None:

        stg_mask = ['01', '02', '04', '08', '10', '20', '40', '80']
        values = {str(k): v for k, v in enumerate((f'{i}{j * "00"}' for j in range(8) for i in stg_mask), 1)}
        return values.get(val)

    def convert_values_flash_dark(self, val):
        converted_values_flash_dark = {
            '1': '2', 'true': '2', 'on': '2', 'вкл': '2', '2': '2',
            '0': '0', 'false': '0', 'off': '0', 'выкл': '0',
        }
        return converted_values_flash_dark.get(val)

    """ GET REQUEST """

    def _mode_define(self, utcType2OperationMode: str, isFlash: str, isDark: str,
                     isManual: str, plan: str, hasDetErrors: str, localAdaptiv: str) -> str:
        """ Определяет текщий ружим ДК.
        :arg equipment_status (str): Текущий режим работы контроллера:
                                     workingProperly(1),
                                     powerUp(2),
                                     dark(3),
                                     flash(4),
                                     partialFlash(5),
                                     allRed(6)

        :arg plan (str): Текущий номер плана
        :arg softstat180_181 (str): Текущее состояние входов 180 и 181
        :arg num_logics (str): Количество детекторных логик

        :return str: Возращает текущий режим ДК(Фикс/Адаптива/КУ и т.д)
        """


        if isFlash is not None and isFlash.isdigit() and int(isFlash) in range(1, 5):
            val_mode = '4'
        elif isDark == '1':
            val_mode = '3'
        elif isManual == '1':
            val_mode = '10'
        elif utcType2OperationMode == '3' and plan == '0':
            val_mode = '11'
        elif localAdaptiv == '1' and hasDetErrors == '0' and plan != '0':
            val_mode = '8'
        elif (localAdaptiv == '0' or hasDetErrors == '1') and plan != '0':
            val_mode = '12'
        else:
            val_mode = '--'
        return self.statusMode.get(val_mode)

    def get_current_mode(self, varBinds: list) -> tuple:
        utcType2OperationMode = hasErrors = isFlash = isDark = isManual = plan = stage = \
            hasDetErrors = localAdaptiv = None

        new_varBins = []
        for data in varBinds:
            oid, val = data[0].__str__(), data[1].prettyPrint()
            oid = oid.replace(self.scn, '') if oid.endswith(self.scn) else oid
            user_oids = self.req_data.get(EntityJsonResponce.REQUEST_ENTITY.value)
            if oid in self.get_state_oids:
                if oid == Oids.utcType2OperationMode.value:
                    utcType2OperationMode = val
                elif oid == Oids.utcReplyCF.value:
                    hasErrors = val
                elif oid == Oids.utcReplyFR.value:
                    isFlash = val
                elif oid == Oids.potokP_utcReplyDarkStatus.value:
                    isDark = val
                elif oid == Oids.utcReplyMC.value:
                    isManual = val
                elif oid == Oids.potokP_utcReplyPlanStatus.value:
                    plan = val
                elif oid == Oids.utcReplyGn.value:
                    stage = self.convert_val_to_num_stage_get_req(val)
                elif oid in Oids.utcReplyDF.value:
                    hasDetErrors = val
                elif oid in Oids.potokP_utcReplyLocalAdaptiv.value:
                    localAdaptiv = val
                if user_oids is not None and Oids(oid).name in user_oids:
                    new_varBins.append(data)
            else:
                new_varBins.append(data)
        mode = self._mode_define(utcType2OperationMode, isFlash, isDark, isManual, plan, hasDetErrors, localAdaptiv)
        basic_curr_state = {EntityJsonResponce.BASIC_STATE.value: {
            EntityJsonResponce.CURRENT_MODE.value: mode,
            EntityJsonResponce.CURRENT_STAGE.value: str(stage),
            EntityJsonResponce.CURRENT_PLAN.value: plan,
        }
        }
        return new_varBins, basic_curr_state

    """*******************************************************************
    ***                          SET-REQUEST                          ****   
    **********************************************************************
    """

    async def set_stage(self, value='0', timeout=0, retries=0):
        """"
        Устанавливает  фазу.
        :param value:  Номер фазы в десятичном виде
        :param retries:
        :param timeout:
        :return: ErrorIndication, varBinds
        """
        self.set_entity[inspect.stack()[0][3]] = value
        if not self.scn:
            self.scn = await self.get_scn()

        if value.lower() in {'0', 'локал', 'false', 'сброс', 'reset'}:
            oids = (
                (Oids.utcType2OperationMode.value, Integer32(1)),
                (Oids.utcControlTO.value + self.scn, Integer32(0)),
            )
        else:
            converted_val = self.convert_val_to_num_stage_set_req(value)
            oids = [
                (Oids.utcType2OperationModeTimeout.value, Integer32(90)),
                (Oids.utcType2OperationMode.value, Integer32(3)),
                (Oids.utcControlTO.value + self.scn, Integer32(1)),
                (Oids.utcControlFn.value + self.scn, OctetString(hexValue=converted_val)),
            ]
        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)

    async def set_dark(self, value='0', timeout=0, retries=0):
        """"
        Устанавливает  фазу.
        :param value:  Номер фазы в десятичном виде
        :param retries:
        :param timeout:
        :return: ErrorIndication, varBinds
        """
        self.set_entity[inspect.stack()[0][3]] = value
        if not self.scn:
            self.scn = await self.get_scn()

        oids = (
            (Oids.utcType2OperationMode.value, Integer32(3)),
            (Oids.utcControlTO.value + self.scn, Integer32(1)),
            (Oids.utcControlLO.value + self.scn, Integer32(self.convert_values_flash_dark(value))),
        )

        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)

    async def set_flash(self, value='0', timeout=0, retries=0):
        """"
        Устанавливает  фазу.
        :param value:  Номер фазы в десятичном виде
        :param retries:
        :param timeout:
        :return: ErrorIndication, varBinds
        """
        self.set_entity[inspect.stack()[0][3]] = value
        if not self.scn:
            self.scn = await self.get_scn()

        oids = (
            (Oids.utcType2OperationMode.value, Integer32(3)),
            (Oids.utcControlTO.value + self.scn, Integer32(1)),
            (Oids.utcControlFF.value + self.scn, Integer32(self.convert_values_flash_dark(value))),
        )

        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)

    async def set_restart_program(self, value='1', timeout=0, retries=0):
        self.set_entity[inspect.stack()[0][3]] = value
        if not self.scn:
            self.scn = await self.get_scn()
        oids = (
            (Oids.potokP_utcControRestartProgramm.value + self.scn, Integer32(value)),
        )
        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)


class PeekUG405(BaseUG405):

    def __init__(self, ip_adress, host_id=None, scn=None):
        super().__init__(ip_adress, scn, host_id)
        self.set_controller_type()

    """ SET REQUEST """

    async def set_stage(self, value='0', timeout=1, retries=1):
        """"
        Устанавливает  фазу.
        :param value:  Номер фазы в десятичном виде
        :param retries:
        :param timeout:
        :return: ErrorIndication, varBinds
        """
        self.set_entity[inspect.stack()[0][3]] = value
        if not self.scn:
            self.scn = await self.get_scn()

        if value.lower() in {'0', 'локал', 'false', 'сброс', 'reset'}:
            oids = [
                (Oids.utcType2OperationMode.value, Integer32(1)),
                (Oids.utcControlTO.value + self.scn, Integer32(0)),
            ]
            return await self.set_request_base(
                self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries
            )

        converted_val = self.convert_val_to_num_stage_set_req(value)
        curr_operation_mode = await self.get_operation_mode()

        if curr_operation_mode == '1':
            await self.set_operation_mode('2')
            await self.set_operation_mode('3')

        oids = [
            (Oids.utcType2OperationModeTimeout.value, Integer32(90)),
            (Oids.utcType2OperationMode.value, Integer32(3)),
            (Oids.utcControlTO.value + self.scn, Integer32(1)),
            (Oids.utcControlFn.value + self.scn, OctetString(hexValue=converted_val)),
        ]
        return await self.set_request_base(self.ip_adress, self.community_write, oids, timeout=timeout, retries=retries)

    async def set_flash(self, value='0', timeout=1, retries=1):
        """
            Устанавливает жёлтое мигание.
            :param timeout: Таймаут подключения
            :param retries: Количетсво попыток подключения
            :param value -> В аргумент необходимо передавать значение 1 или 0.
        """

        pass

    async def set_dark(self, value=0, timeout=1, retries=1):
        """
            Устанавливает жёлтое ос.
            :param timeout: Таймаут подключения
            :param retries: Количетсво попыток подключения
            :param value -> В аргумент необходимо передавать значение 1 или 0.
        """

        pass


"""" SSH MANAGEMENT """


class ConnectionSSH(BaseCommon):
    access_levels = {
        'swarco_itc': (os.getenv('swarco_itc_login'), os.getenv('swarco_itc_passwd')),
        'swarco_r': (os.getenv('swarco_r_login'), os.getenv('swarco_r_passwd')),
        'peek_r': (os.getenv('peek_r_login'), os.getenv('peek_r_passwd')),
    }

    def __init__(self, ip_adress, host_id=None):
        super().__init__(ip_adress, host_id)
        self.set_controller_type()

    @classmethod
    def create_ssh_session(cls, ip_adress, access_level):

        login, password = cls.access_levels.get(access_level)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(hostname=ip_adress,
                           username=login,
                           password=password,
                           timeout=4,
                           look_for_keys=False, allow_agent=False)
            message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} < Соединение установлено >'
        except paramiko.ssh_exception.NoValidConnectionsError as err:
            client = None
            message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Не удалось установить соединение с хостом...'
        except paramiko.ssh_exception.AuthenticationException as err:
            client = None
            message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Ошибка авторизации...'
        except TimeoutError as err:
            client = None
            message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Ошибка таймаута подключения...'
        except:
            client = None
            message = f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} Программный сбой подключения...'
        return client, message

    @staticmethod
    async def read_timed(stream: asyncssh.SSHReader,
                         timeout: float = 1,
                         bufsize: int = 1024) -> str:
        """Read data from a stream with a timeout."""
        ret = ''
        while True:
            try:
                ret += await asyncio.wait_for(stream.read(bufsize), timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                return ret

    async def acreate_connect(self, ip: str, username: str, password: str) -> tuple:
        """
        :param ip:
        :param username:
        :param password:
        :return: (None, asyncssh.connection.SSHClientConnection), если соедиенение успешно, иначе
                 (errorIndication, None)
        """

        connect = errorIndication = None
        try:
            timeout = asyncssh.SSHClientConnectionOptions(login_timeout=10)
            connect = await asyncssh.connect(
                host=ip,
                username=username,
                password=password,
                # options=timeout,
                kex_algs=os.getenv('kex_algs'),
                encryption_algs=os.getenv('enc_algs'),
                known_hosts=None
            )
            return errorIndication, connect
        except asyncssh.misc.PermissionDenied:
            errorIndication = 'Permission denied'
        except (OSError, asyncssh.Error) as exc:
            errorIndication = 'SSH connection failed'
        except Exception as err:
            errorIndication = err
            logger.error('Ошибка выполнения программы: {}'.format(err))
        finally:
            # logger.debug(connect)
            return errorIndication, connect


    async def adownload_scp(self, access_level: str, files: list[str], dest_path: str = '.'):
        login, passwd = self.access_levels.get(access_level)
        errorIndication, conn = await self.acreate_connect(
            ip=self.ip_adress,
            username=login,
            password=passwd
        )
        if errorIndication:
            return errorIndication, [], self
        data = [(conn, file) for file in files]

        dest_path = Path(self.reverse_slashes(f'{dest_path}/{self.ip_adress}/{self.set_curr_datetime(sep="-")}'))

        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        else:
            await asyncio.sleep(0.5)
            os.makedirs(dest_path)
        try:
            await asyncssh.scp(data, dest_path)
            errorIndication = None
            return errorIndication, dest_path, self
        except (OSError, asyncssh.Error) as exc:
            errorIndication = 'SFTP operation failed: ' + str(exc)
            return errorIndication, dest_path, self
        except Exception as err:
            return err, (dest_path, os.listdir(dest_path)[-1]), self
        finally:
            conn.close()


class SwarcoSSHBase(ConnectionSSH):
    first_man_inp: int = int(os.getenv('first_man_inp'))
    man_inp = first_man_inp + 1
    first_inp_stage = first_man_inp + 3
    last_inp_stage = int(os.getenv('last_inp_stage'))
    first_hardw_inp = os.getenv('start_hardw_input')
    flash_enable = os.getenv('flash_enable')
    flash_disable = os.getenv('flash_disable')
    signals_on = os.getenv('signals_on')
    signals_off = os.getenv('signals_off')
    btn_local_enable = os.getenv('btn_local_enable')
    btn_local_disable = os.getenv('btn_local_disable')
    stdout_encoding = os.getenv('stdout_encoding')
    stdout_decoding = os.getenv('stdout_decoding')
    term_type = os.getenv('term_type')
    proc_ssh_encoding = os.getenv('proc_ssh_encoding')
    user_itc = os.getenv('user_itc')
    inputs_curr_state = os.getenv('inputs_curr_state')
    inps_ = os.getenv('hardw_inp')

    inp_stages = {
        str(stage): str(inp) for stage, inp in zip(range(1, 9), range(first_inp_stage, last_inp_stage))
    }
    synonyms = {
        '1': '1', 'true': '1', 'вкл': '1', 'on': '1',
        '0': '0', 'false': '0', 'off': '0', 'выкл': '0'
    }

    def make_any_commands(self, commands_from_user, separ=','):
        return (command + '\n' for command in commands_from_user.split(separ))

    def commands_set_stage(self, num_stage):
        return (
            f'{self.inps_}{self.man_inp}=1\n', f'{self.inps_}{self.inp_stages.get(num_stage)}=1\n'
        )

    def commands_open_level2(self) -> tuple:
        return f'{os.getenv("lang_to_uk")}\n', f'{os.getenv("level2_login")}\n', f'{os.getenv("level2_passwd")}\n'

    def commands_reset_man_stages_inputs(self) -> Generator:
        return (f'{self.inps_}{inp}=0\n' for inp in range(self.first_inp_stage, self.last_inp_stage))

    def commands_set_flash(self) -> Generator:
        return (
            f'{self.inps_}{inp}=0\n' if inp > self.man_inp + 1 else f'{self.inps_}{inp}=1\n'
            for inp in range(self.man_inp, self.last_inp_stage)
        )

    def commands_set_dark(self) -> Generator:
        return (
            f'{self.inps_}{inp}=0\n' if inp > self.man_inp else f'{self.inps_}{inp}=1\n'
            for inp in range(self.first_man_inp, self.last_inp_stage)
        )

    def commands_reset_man_inputs(self) -> Generator:
        return (f'{self.inps_}{inp}=0\n' for inp in range(self.man_inp, self.last_inp_stage))

    def commands_button_flash_on(self) -> tuple:
        return f'{self.flash_enable}\n',

    def commands_button_flash_off(self) -> tuple:
        return f'{self.flash_disable}\n',

    def commands_button_signals_on(self):
        return f'{self.signals_on}\n',

    def commands_button_signals_off(self):
        return f'{self.signals_off}\n',

    def commands_button_local_on(self):
        return f'{self.btn_local_enable}\n',

    def commands_button_local_off(self):
        return f'{self.btn_local_disable}\n',

    @staticmethod
    def parse_command_itc(data: list) -> dict:
        """
        :param data:
        :return:

        Пример itc(data):

        &&>  Intersection: leninskiy-7_8_9-
        Customer: noviy_pr-d
        ID: 13379 TZ_1338_2020
        System time: 2024-10-29 21:48:13
        P15CB MANUAL
        I1: Flash/Manual [err] OFF 225V 12.1V +32C
        ITC-2 v6.94.2 Copyright (c) 2006-2011 Swarco
        Current errors:
        2024-10-29 17:35:35	+	95-001-000	User defined error 95: 1, 0

        """

        itc_part = {}
        for i, line in enumerate(data):
            if i == 8:
                break
            line = line.strip().replace("&&> \u0000", '') if line.startswith('&&') else line.strip()
            if ':' in line and 'Current errors:' not in line:
                k, v = line.split(':', maxsplit=1)
                itc_part |= {k: v.lstrip()}
            elif i == 4:
                itc_part |= {'State': line.lstrip()}
            elif i == 6:
                itc_part |= {'Firmware': line.lstrip()}
            elif i == 7:
                itc_part |= {line.lstrip(): data[i + 1].replace("+\t", '').replace("\t", ' | ')}
        return itc_part

    @staticmethod
    def parse_command_instat(data: list) -> dict:
        logger.debug(data)
        if not data and len(data) != 2:
            return {}
        return {data[0].replace(" ", '')[:11]: data[1].replace(" ", '').split(':')[-1][:11]}

    async def send_commands(self, commands: Iterator) -> tuple:
        """

        :param commands: Список комманд, которые будут отправлены в shell
        :return: errorIndication, stdout(вывод сеанса shell)
        """

        self.put_to_req_data({'protocol': 'ssh', 'type': 'set', 'request_time': self.set_curr_datetime()})

        logger.debug(commands)
        login, passwd = self.access_levels.get('swarco_itc')
        errorIndication, conn = await self.acreate_connect(
            ip=self.ip_adress,
            username=login,
            password=passwd
        )
        if errorIndication:
            return errorIndication, []

        errorIndication = stdout = commands_for_json = None
        try:
            commands_for_json = []
            async with conn.create_process(term_type=self.term_type, encoding=self.proc_ssh_encoding) as proc:
                await self.read_timed(proc.stdout, timeout=3, bufsize=4096)
                for command in commands:
                    # logger.debug(command)
                    commands_for_json.append(command)
                    proc.stdin.write(command)
                response = await self.read_timed(proc.stdout, timeout=3, bufsize=4096)
                proc.stdin.write('exit\n')
                errorIndication, stdout = None, response
        except (OSError, asyncssh.Error):
            errorIndication = 'SSH connection failed'
        finally:
            self.responce_time = self.set_curr_datetime()
            conn.close()
            return errorIndication, [commands_for_json, stdout]


class AsyncSetInputsSwarcoSSH(SwarcoSSHBase):

    async def set_stage(self, num_stage):

        self.set_entity[inspect.stack()[0][3]] = num_stage
        if num_stage in {str(i) for i in range(1, 9)}:
            commands = itertools.chain(self.commands_open_level2(), self.commands_reset_man_inputs(),
                                       self.commands_set_stage(num_stage),
                                       (f'{self.inputs_curr_state}{self.first_hardw_inp} ?\n', f'{self.user_itc}\n'))
        else:
            commands = itertools.chain(self.commands_open_level2(), self.commands_reset_man_inputs(),
                                       (f'{self.inputs_curr_state}{self.first_hardw_inp} ?\n', f'{self.user_itc}\n'))
        errorIndication, response = await self.send_commands(commands)
        logger.debug(self.req_data)
        logger.debug(self.set_entity)
        return errorIndication, response, self

    async def set_flash(self, val):
        self.set_entity[inspect.stack()[0][3]] = val

        if self.synonyms.get(val) == '1':
            commands = itertools.chain(self.commands_open_level2(), self.commands_reset_man_inputs(),
                                       self.commands_set_flash(), (f'{self.inputs_curr_state}{self.first_hardw_inp} ?\n',))
        else:
            commands = itertools.chain(self.commands_open_level2(), self.commands_reset_man_inputs(),
                                       (f'{self.inputs_curr_state}{self.first_hardw_inp} ?\n',))
        errorIndication, response = await self.send_commands(commands)
        logger.debug(self.req_data)
        logger.debug(self.set_entity)
        return errorIndication, response, self

    async def set_dark(self, val):
        self.set_entity[inspect.stack()[0][3]] = val

        if self.synonyms.get(val) == '1':
            commands = itertools.chain(self.commands_open_level2(), self.commands_reset_man_inputs(),
                                       self.commands_set_dark(), (f'{self.inputs_curr_state}{self.first_hardw_inp} ?\n',))
        else:
            commands = itertools.chain(self.commands_open_level2(), self.commands_reset_man_inputs(),
                                       (f'{self.inputs_curr_state}{self.first_hardw_inp} ?\n',))
        errorIndication, response = await self.send_commands(commands)
        logger.debug(self.req_data)
        logger.debug(self.set_entity)
        return errorIndication, response, self

    def parse_varBinds(self, varBinds: list) -> tuple:
        """

        :param varBinds: Список. Состоит из 2 элементов.
                         varBinds[0]: команды, отправленные в shell
                         varBinds[1]: stdout из shell
        :return: часть для json
        """
        string_fragment_instat = '1234567890' * 7
        string_fragment_itc = 'Intersection:'
        flag_instat = flag_itc = False

        sent_commands, curr_state_inps101_111, itc = [], {}, []
        if varBinds[0]:
            for data in varBinds[0]:
                if 'inp' in data:
                    command, val = data.strip().split('=')
                    sent_commands.append({command: val})
        if varBinds[1]:
            stdout = varBinds[1].encode(self.stdout_encoding).decode(self.stdout_decoding).splitlines()
            logger.debug(stdout)
            for i, line in enumerate(stdout):
                logger.info((i, line))
                try:
                    if not flag_instat and string_fragment_instat in line and ':' in stdout[i + 1]:
                        curr_state_inps101_111 = self.parse_command_instat(stdout[i:i + 2])
                        flag_instat = True
                    if not flag_itc and string_fragment_itc in line:
                        itc = self.parse_command_itc(stdout[i:i + 10])
                        flag_itc = True
                except IndexError:
                    logger.critical('Неправильно сформирован stdout из ssh AsyncSetInputsSwarcoSSH')
        return sent_commands, [{'inputs': curr_state_inps101_111}, {'itc': itc}]


class AsyncPushButtonSwarcoSSH(SwarcoSSHBase):

    async def set_flash(self, val: str) -> tuple:
        self.set_entity[inspect.stack()[0][3]] = val

        if self.synonyms.get(val) == '1':
            commands = itertools.chain(self.commands_open_level2(), self.commands_button_flash_on(), (f'{self.user_itc}\n',))
        else:
            commands = itertools.chain(self.commands_open_level2(), self.commands_button_flash_off(), (f'{self.user_itc}\n',))
        errorIndication, response = await self.send_commands(commands)
        logger.debug(self.req_data)
        logger.debug(self.set_entity)
        return errorIndication, response, self

    async def set_dark(self, val: str) -> tuple:
        self.set_entity[inspect.stack()[0][3]] = val

        if self.synonyms.get(val) == '1':
            commands = itertools.chain(self.commands_open_level2(), self.commands_button_signals_on(), (f'{self.user_itc}\n',))
        else:
            commands = itertools.chain(self.commands_open_level2(), self.commands_button_signals_off(), (f'{self.user_itc}\n',))
        errorIndication, response = await self.send_commands(commands)
        logger.debug(self.req_data)
        logger.debug(self.set_entity)
        return errorIndication, response, self

    async def set_local(self, val: str) -> tuple:
        self.set_entity[inspect.stack()[0][3]] = val

        if self.synonyms.get(val) == '1':
            commands = itertools.chain(self.commands_open_level2(), self.commands_button_local_on(), (f'{self.user_itc}\n',))
        else:
            commands = itertools.chain(self.commands_open_level2(), self.commands_button_local_off(), (f'{self.user_itc}\n',))
        errorIndication, response = await self.send_commands(commands)
        logger.debug(self.req_data)
        logger.debug(self.set_entity)
        return errorIndication, response, self

    async def set_signals(self, val: str) -> tuple:
        self.set_entity[inspect.stack()[0][3]] = val

        if self.synonyms.get(val) == '1':
            commands = itertools.chain(self.commands_open_level2(), self.commands_button_signals_on(), (f'{self.user_itc}\n',))
        else:
            commands = itertools.chain(self.commands_open_level2(), self.commands_button_signals_off(), (f'{self.user_itc}\n',))
        errorIndication, response = await self.send_commands(commands)
        logger.debug(self.req_data)
        logger.debug(self.set_entity)
        return errorIndication, response, self

    def parse_varBinds(self, varBinds: list) -> tuple:
        """

        :param varBinds: Список. Состоит из 2 элементов.
                         varBinds[0]: команды, отправленные в shell
                         varBinds[1]: stdout из shell
        :return: часть для json
        """
        string_fragment_itc = 'Intersection:'
        flag_itc = False
        sent_commands, itc = [], {}
        stdout = varBinds[1].encode(self.stdout_encoding).decode(self.stdout_decoding).splitlines()
        # logger.debug(stdout)
        for i, line in enumerate(stdout):
            if not flag_itc and string_fragment_itc in line:
                command, val = stdout[i - 1].split(':')
                sent_commands.append({command.lstrip().replace("&&> \x00", ''): val.lstrip()})
                itc = self.parse_command_itc(stdout[i:i + 10])
                flag_itc = True
        return sent_commands, [{'itc': itc}]


class AsyncGetItcDataSSH(SwarcoSSHBase):
    """
    Класс получения и обработки stdout из shell для команды itc
    """

    async def get_states(self) -> tuple:
        """
        Метод получает stdout из оболочки shell в виде текста сеанса для команды itc.
        :return: кортеж вида (ошибка, stdout из shell, объект)
        """

        self.put_to_get_entity('get_states')
        self.put_to_req_data({
            EntityJsonResponce.PROTOCOL.value: EntityJsonResponce.SSH.value,
            EntityJsonResponce.TYPE.value: EntityJsonResponce.GET.value,
            EntityJsonResponce.REQUEST_TIME.value: self.set_curr_datetime()
        })

        commands = itertools.chain(self.commands_open_level2(), (f'{self.user_itc}\n',))
        errorIndication, response = await self.send_commands(commands)
        return errorIndication, response, self

    def parse_varBinds(self, varBinds: list):
        """
        Метод парсит данные о состоянии контроллера для itc из shell
        :param varBinds: Список. Состоит из 2 элементов.
                         varBinds[0]: команды, отправленные в shell
                         varBinds[1]: stdout из shell
        :return: часть для json
        """

        string_fragment_itc = 'Intersection:'
        flag_itc = False
        sent_commands = [s.strip() for s in varBinds[0]] if varBinds[0] else []
        logger.debug(sent_commands)
        itc = {}
        stdout = varBinds[1].encode(self.stdout_encoding).decode(self.stdout_decoding).splitlines()
        for i, line in enumerate(stdout):
            if not flag_itc and string_fragment_itc in line:
                itc = self.parse_command_itc(stdout[i:i + 10])
                flag_itc = True
        return {'itc': itc}


"""" WEB MANAGEMENT """


class PeekWeb(BaseCommon):

    MAN_INPUTS_MPP_PH = {mpp_inp for mpp_inp in os.getenv('MAN_INPUTS').split()}
    ALL_MPP_INPUTS = tuple(mpp_inp for mpp_inp in os.getenv('ALL_MAN_INPUTS').split())
    MAN_INPUTS_STAGES = {man_inp[-1]: man_inp for man_inp in MAN_INPUTS_MPP_PH} | {'0': 'reset_man'}

    START_NAME_MAN = os.getenv('START_NAME_MAN')
    MAN, MAN_FLASH, MAN_OFF = ALL_MPP_INPUTS[:3]
    MAN_STAGE1, MAN_STAGE2, MAN_STAGE3, MAN_STAGE4, MAN_STAGE5, MAN_STAGE6, MAN_STAGE7, MAN_STAGE8 = ALL_MPP_INPUTS[3:]

    CP_AUTO = os.getenv('CP_AUTO')
    CP_OFF = os.getenv('CP_OFF')
    CP_FLASH = os.getenv('CP_FLASH')
    CP_RED = os.getenv('CP_RED')

    ALLOWED_INPUTS = {mpp_inp for mpp_inp in os.getenv('ALL_INPUTS').split()}

    ACTUATOR_RESET = os.getenv('ACTUATOR_RESET')
    ACTUATOR_OFF = os.getenv('ACTUATOR_OFF')
    ACTUATOR_ON = os.getenv('ACTUATOR_ON')
    ACTUATOR_RESET_NAME = os.getenv('ACTUATOR_RESET_NAME')
    ACTUATOR_OFF_NAME = os.getenv('ACTUATOR_OFF_NAME')
    ACTUATOR_ON_NAME = os.getenv('ACTUATOR_ON_NAME')

    ACTUATOR_VALUES = {
        ACTUATOR_RESET_NAME: ACTUATOR_RESET,
        ACTUATOR_OFF_NAME: ACTUATOR_OFF,
        ACTUATOR_ON_NAME: ACTUATOR_ON
    }
    ACTUATOR_VALUES_INVERT = {
        ACTUATOR_RESET: ACTUATOR_RESET_NAME,
        ACTUATOR_OFF: ACTUATOR_OFF_NAME,
        ACTUATOR_ON: ACTUATOR_ON_NAME
    }

    synonyms_red_yellow_dark = {
        '1': 'ВКЛ',
        '0': 'ВФ'
    }

    INPUTS = 'INPUTS'
    USER_PARAMETERS = 'USER_PARAMETERS'
    CURRENT_STATE = 'STATE'

    GET_INPUTS_CONTENT = 'GET_INPUTS'
    SET_INPUTS = 'SET_INPUTS'
    GET_USER_PARAMETERS_CONTENT = 'GET_USER_PARAMETERS'
    SET_USER_PARAMETERS = 'SET_USER_PARAMETERS'
    GET_CURRENT_STATE = 'GET_CURRENT_STATE'

    ROUTE_GET_INPUTS = os.getenv('ROUTE_GET_INPUTS')
    ROUTE_SET_INPUTS = os.getenv('ROUTE_SET_INPUTS')
    ROUTE_GET_USER_PARAMETERS = os.getenv('ROUTE_GET_USER_PARAMETERS')
    ROUTE_SET_USER_PARAMETERS = os.getenv('ROUTE_SET_USER_PARAMETERS')
    ROUTE_GET_CURRENT_STATE = os.getenv('ROUTE_GET_CURRENT_STATE')

    routes_url = {
        GET_INPUTS_CONTENT: ROUTE_GET_INPUTS,
        SET_INPUTS: ROUTE_SET_INPUTS,
        GET_USER_PARAMETERS_CONTENT: ROUTE_GET_USER_PARAMETERS,
        SET_USER_PARAMETERS: ROUTE_SET_USER_PARAMETERS,
        GET_CURRENT_STATE: ROUTE_GET_CURRENT_STATE
    }

    routes_url_matches = {
        routes_url.get(GET_INPUTS_CONTENT): GET_INPUTS_CONTENT,
        routes_url.get(GET_USER_PARAMETERS_CONTENT): GET_USER_PARAMETERS_CONTENT,
        routes_url.get(GET_CURRENT_STATE): GET_CURRENT_STATE,
    }

    INPUT_NAME_FOR_SET_VAL = os.getenv('INPUT_NAME_FOR_SET_VAL')
    USER_PARAM_NAME_FOR_SET_VAL = os.getenv('USER_PARAM_NAME_FOR_SET_VAL')

    headers = {
        'User-Agent': os.getenv('user_agent')
    }
    cookies = {os.getenv('peek_web_k'): os.getenv('peek_web_v')}

    JSON_SET_COMMAND_BODY = (
        EntityJsonResponce.RESULT.value,
        EntityJsonResponce.TYPE_COMMAND.value,
        EntityJsonResponce.VALUE.value
    )

    def __init__(self, ip_adress: str, host_id: str = None):
        super().__init__(ip_adress, host_id)
        self.ip_adress = ip_adress
        self.host_id = host_id
        self.controller_type = AvailableControllers.PEEK.value
        self.last_read_parameters = {}
        self.last_set_commands = []

    def put_to_last_val(self, data):
        self.last_set_commands.append(data)

    async def set_val_to_web(self, type_set_request, session, data_params, ):

        index, value = data_params
        logger.debug(data_params)

        if type_set_request == self.SET_INPUTS:
            self.put_to_last_val({self.last_read_parameters.get(index): self.ACTUATOR_VALUES_INVERT.get(value)})
            params = {'par_name': f'{self.INPUT_NAME_FOR_SET_VAL}{index}', 'par_value': value}
            url = f'http://{self.ip_adress}{self.routes_url.get(self.SET_INPUTS)}'
        elif type_set_request == self.SET_USER_PARAMETERS:
            self.put_to_last_val({self.last_read_parameters.get(index): value})
            url = f'http://{self.ip_adress}{self.routes_url.get(self.SET_USER_PARAMETERS)}'
            params = {'par_name': f'{self.USER_PARAM_NAME_FOR_SET_VAL}{index}', 'par_value': value}
        else:
            raise TypeError

        async with session.post(url=url, data=params) as response:
            await response.text()
            return response.status


class PeekWebContent(PeekWeb):
    """
    Интерфейс взаимодейтсвия по получению веб контента через http запросы
    """

    async def fetch(self, route: str, session: aiohttp.ClientSession, timeout: aiohttp.ClientTimeout):
        async with session.get(route, timeout=timeout) as responce:
            if responce.status != 200:
                raise TypeError(EntityJsonResponce.TYPE_CONTROLLER_ERROR_MSG.value)
            return await responce.text()

    async def get_content_from_web_multiple(self, routes: list, timeout=2) -> tuple[str | None, list[asyncio.Task]]:
        """
        Метод формирует запрос на веб страницу для получения контента по заданным маршрутам
        :param routes: список маршрутов страниц, по которым необходимо получить контент страницы
        :param timeout: таймаут http сессии
        :return: кортеж вида: индекс 0: error_indication == None если нет ошибки, иначе строку с текстом ошибки,
                              индекс 1: список завершенных задач
        """
        url = f'http://{self.ip_adress}'
        errorIndication = None
        try:
            timeout = aiohttp.ClientTimeout(timeout)
            async with aiohttp.ClientSession(
                    url, headers=self.headers, cookies=self.cookies, timeout=timeout
            ) as session:
                async with asyncio.TaskGroup() as tg:
                    content = [
                        tg.create_task(
                            self.fetch(route, session, timeout), name=self.routes_url_matches.get(route))
                        for route in routes
                    ]
        finally:
            return errorIndication or self.has_error_in_taskgroup(content), content

    def parse_current_mode(self, content: dict):
        """
        Обрабатывает контент с главной страницы и формирует словарь с данными о состоянии дк
        :param content: словарь с контетом страниц
        :return: словарь для json responce поля basic
        Пример:
        basic_curr_state = EntityJsonResponce.BASIC_STATE.value: {
            "current_plan": "002",
            "current_parameter_plan": "002",
            "current_time": "2024-11-25 01:25:23",
            "current_errors": "SDET,MIMC,UNIT",
            "streams": 4,
            "stream_info": {
                "1": {
                    "current_mode": "FT",
                    "current_stage": "4",
                    "current_state": "УПРАВЛЕНИЕ"
                },
                "2": {
                    "current_mode": "FT",
                    "current_stage": "6",
                    "current_state": "УПРАВЛЕНИЕ"
                },
                "3": {
                    "current_mode": "FT",
                    "current_stage": "8",
                    "current_state": "УПРАВЛЕНИЕ"
                },
                "4": {
                    "current_mode": "FT",
                    "current_stage": "10",
                    "current_state": "УПРАВЛЕНИЕ"
                }
            }
        }
        """

        try:
            content_curr_state = content.pop(self.GET_CURRENT_STATE)
        except KeyError:
            return content

        flag_head, streams_cnt = True, 0
        basic, all_streams_data, curr_stream_data = {}, {}, {}
        curr_plan = curr_plan_param = curr_time = curr_alarms = current_state = current_mode = curr_stage = None
        for line in content_curr_state.splitlines():
            if flag_head:
                if ':D;;##T_PLAN##;' in line:
                    curr_plan = line.split(':D;;##T_PLAN##;')[-1].split(maxsplit=1)[0]
                    continue
                elif '##T_TIMINGSET##;' in line:
                    curr_plan_param = line.split('##T_TIMINGSET##;')[-1]
                    continue
                elif ':D;;##T_TIME##;' in line:
                    curr_time = line.split(':D;;##T_TIME##;')[-1]
                    continue
                elif ':D;;##T_ALARMS##;' in line:
                    curr_alarms = line.split(':D;;##T_ALARMS##;')[-1]
                    continue
                elif ':ENDTABLE' in line:
                    flag_head = False
                    basic = {
                        EntityJsonResponce.CURRENT_PLAN.value: curr_plan,
                        EntityJsonResponce.CURRENT_PARAM_PLAN.value: curr_plan_param,
                        EntityJsonResponce.CURRENT_TIME.value: curr_time,
                        EntityJsonResponce.CURRENT_ERRORS.value: curr_alarms,
                    }
                    continue
                continue

            elif '<b>##T_STREAM##' in line:
                streams_cnt += 1
                continue
            elif ':D;;##T_STATE##;' in line:
                current_state = line.split(':D;;##T_STATE##;')[-1]
                continue
            elif '(##T_STAGE##);' in line:
                current_mode, curr_stage = line.split('(##T_STAGE##);')[-1].split()
                curr_stage = curr_stage.replace('(', '').replace(')', '')
                continue
            elif ':ENDTABLE' in line:
                curr_stream_data[streams_cnt] = {
                    EntityJsonResponce.CURRENT_MODE.value: current_mode,
                    EntityJsonResponce.CURRENT_STAGE.value: curr_stage,
                    EntityJsonResponce.CURRENT_STATE.value: current_state,
                }
                all_streams_data |= curr_stream_data
                current_state = current_mode = curr_stage = None
                continue
            elif '<h2>' in line:
                basic['streams'] = streams_cnt
                basic['stream_info'] = all_streams_data
                break

        basic_curr_state = {
            EntityJsonResponce.BASIC_STATE.value: basic
        }

        return content, basic_curr_state

    def get_current_mode(self, content: dict) -> dict:
        """
        Метод для формирования данных о текущем режиме ДК
        :param content: словарь из контента веб страниц
        :return: обработанные данные для json responce
        """

        return self.parse_current_mode(content)

    def parse_inps_and_user_param_content(self, content: str, create_self_attr: bool = False):

        parsed_data = {}
        logger.debug(content)
        for line in (
                line.split(';')[1:] for line in content.splitlines() if line.startswith(':D')
        ):
            index, num, name, val1, val2, val3 = line
            # val1, val2 и val3 зависят от типа получаемых данных.
            # если получаем ВВОДЫ:
            # val1 -> Состояние val2 -> Время, val3 -> АКТУАТОР
            # если Параметры программы:
            # val1 -> Значение, val2 -> Мин. val3 -> Макс
            parsed_data[name] = index, val1, val2, val3

        if create_self_attr:
            # Словарь вводов, где k -> индекс, v -> имя ВВОДА
            self.last_read_parameters = {parsed_data.get(k)[0]: k for k in parsed_data}
        logger.debug(parsed_data)
        logger.debug(self.last_read_parameters)

        return parsed_data

    def varBinds_to_dict(self, varBinds: list[asyncio.Task]) -> dict | list:
        """
        Создает словарь на основе списка вида:
        {имя коррутины(связано с типом веб запроса в методе get_content_from_web_multiple): результат}
        :param varBinds: Список завершенных задач
        :return: в зависимости от типа запроса. для 'get' возврщает словарь вида:
                 {'GET_CURRENT_MODE': ':TITLE;##MENU_001a##\n:SUBTITLE;Moscow: Ховрино / Круг\n:TFT....}
                 для 'set' возвращает список, в котором varBinds[0] это список словарей-отправленных команд,
                 а varBinds[1] это словарь с контентом для разничных страниц подобный словарю, возвращаемому для 'get'

         Пример 'get': {'GET_CURRENT_STATE': ':TITLE;##MENU_001a##\n:SUBTITLE;Moscow: Литовск...}
         Пример 'set': [[{'MPP_PH2': 'ВКЛ'}, {'MPP_MAN': 'ВКЛ'}], {'GET_CURRENT_STATE': ':TITLE;##MENU_001a...}]
        """

        logger.debug(varBinds)
        if self.req_data.get('type') == 'get':
            return {res.get_name(): res.result() for res in varBinds}
        return [varBinds[0], {res.get_name(): res.xp1_result() for res in varBinds[1]}]

    def inputs_to_list_for_json(self, inputs_content: str) -> list:
        p_inp: dict = self.parse_inps_and_user_param_content(inputs_content)
        return [f'{inp}: {p_inp.get(inp)[-1]}' for inp in self.ALL_MPP_INPUTS]

    def user_parameters_to_list_for_json(self, user_parameters_content: str) -> list:
        p_up: dict = self.parse_inps_and_user_param_content(user_parameters_content)
        return [f'{up}: Значение={p_up.get(up)[1]} Мин={p_up.get(up)[2]} Макс={p_up.get(up)[3]}' for up in p_up]


class PeekGetModeWeb(PeekWebContent):
    """
    Интерфейс для получения состояния ДК с главной веб страницы
    """

    async def get_request(self, get_mode: bool = True, timeout=1) -> tuple:
        """
        Метод запроса контента web страницы получения текущего состояния ДК
        :param get_mode: для записи в json responce
        :param timeout: таймаут для сессии http
        :return tuple: (errorIndication, varBinds, объект)
        """
        if get_mode:
            self.put_to_get_entity('get_mode')
            self.put_to_req_data({'protocol': 'http', 'type': 'get', 'request_time': self.set_curr_datetime()})

        errorIndication, content = await self.get_content_from_web_multiple([self.ROUTE_GET_CURRENT_STATE],
                                                                            timeout=timeout)
        self.errorIndication, self.varBinds = errorIndication, content
        # logger.debug(errorIndication)
        # logger.debug(content)
        return errorIndication, content, self


class PeekSetInputsWeb(PeekWebContent):
    """
    Интерфейс для усатновки значений ВВОДОВ через http запрос
    """

    async def set_stage(self, stage_to_set: str, timeout=3) -> tuple:
        """
        Устанавливает фазу методом отправки http запроса (ВВОДЫ)
        :param stage_to_set: номер фазы в десятичном виде
        :param timeout: таймаут http запроса
        :return: кортеж вида errorIndication, [self.last_set_commands, res(контент главной страницы
                 и страницы ВВОДОВ)], self
        """

        self.put_to_req_data({'protocol': 'http', 'type': 'set', 'request_time': self.set_curr_datetime()})
        self.set_entity[inspect.stack()[0][3]] = stage_to_set

        input_name_to_set = self.MAN_INPUTS_STAGES.get(stage_to_set)
        errorIndication, inputs_web_content = await self.get_content_from_web_multiple([self.ROUTE_GET_INPUTS])

        if errorIndication is not None:
            return errorIndication, self.last_set_commands, self

        inputs = self.parse_inps_and_user_param_content(inputs_web_content[0].result(), create_self_attr=True)
        timeout = aiohttp.ClientTimeout(timeout)
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies, timeout=timeout) as session:
            set_CP_AUTO = False
            params_to_set = []
            blocked_inps = [self.MAN_FLASH, self.MAN_OFF]
            for inp in blocked_inps:
                if inputs.get(inp)[1] == '1':
                    set_CP_AUTO = True
                    if inp.startswith(self.START_NAME_MAN):
                        params_to_set.append((inputs.get(inp)[0], self.ACTUATOR_OFF))
                    else:
                        params_to_set.append(params_to_set.append((inputs.get(inp)[0], self.ACTUATOR_RESET)))
            if params_to_set:
                async with asyncio.TaskGroup() as tg1:
                    tasks_res = [
                        tg1.create_task(self.set_val_to_web(self.SET_INPUTS, session, params_to_set)
                                        for _ in params_to_set)
                    ]
                    errorIndication = self.has_error_in_taskgroup(tasks_res)
                    if errorIndication is not None:
                        return errorIndication, [], self

            if set_CP_AUTO:
                res = await self.set_val_to_web(self.SET_INPUTS, session,
                                                (inputs.get(self.CP_AUTO)[0], self.ACTUATOR_RESET))
                if res != 200:
                    errorIndication = EntityJsonResponce.TIMEOUT_ERROR_WEB_REQUEST_MSG.value
                    return errorIndication, [], self
                res = await self.set_val_to_web(self.SET_INPUTS, session,
                                                (inputs.get(self.CP_AUTO)[0], self.ACTUATOR_ON))
                if res != 200:
                    errorIndication = EntityJsonResponce.TIMEOUT_ERROR_WEB_REQUEST_MSG.value
                    return errorIndication, [], self

            async with asyncio.TaskGroup() as tg:
                data_param_to_set = []

                if input_name_to_set == 'reset_man':
                    data_param_to_set.append((inputs.get(self.MAN)[0], self.ACTUATOR_OFF))
                    for inp in self.MAN_INPUTS_MPP_PH:
                        data_param_to_set.append((inputs.get(inp)[0], self.ACTUATOR_RESET))
                else:
                    for inp in inputs:
                        if inp == self.MAN:
                            data_param_to_set.append((inputs.get(inp)[0], self.ACTUATOR_ON))
                        elif (inp in self.MAN_INPUTS_MPP_PH and inp != input_name_to_set
                              and inputs.get(inp)[1] == '1'):
                            data_param_to_set.append((inputs.get(inp)[0], self.ACTUATOR_OFF))
                        elif inp == input_name_to_set:
                            data_param_to_set.append((inputs.get(inp)[0], self.ACTUATOR_ON))
                tasks_res = [tg.create_task(self.set_val_to_web(self.SET_INPUTS, session, data_params))
                             for data_params in data_param_to_set]

            errorIndication = self.has_error_in_taskgroup(tasks_res)
            if errorIndication is not None:
                return errorIndication, self.last_set_commands, self

            errorInd, res = await self.get_content_from_web_multiple(
                [self.ROUTE_GET_CURRENT_STATE, self.ROUTE_GET_INPUTS])
            logger.debug(errorInd)
            logger.debug(res)
            return errorIndication, [self.last_set_commands, res], self

    async def set_val_common(self, timeout=3, inputs_string: str = None, inputs_dict: dict[str, str] = None, **kwargs):
        """
        Устанавливает произвольный ВВОД
        :param timeout: таймаут http запроса
        :param inputs_string: ВВОДЫ можно передать в виде строки. Пример: 'MPP_MAN=ВКЛ;MPP_PH1=ВКЛ'
        :param inputs_dict: ВВОДЫ можно передать в виде словаря. Пример: '{'MPP_MAN': 'ВКЛ', 'MPP_PH1':'ВКЛ'}'
        :param kwargs: ВВОДЫ можно передать в kwargs. Пример: MPP_MAN=ВКЛ, MPP_PH=ВКЛ
        :return:
        """

        set_CP_AUTO = False
        errorIndication, inputs_web_content = await self.get_content_from_web_multiple([self.ROUTE_GET_INPUTS])

        if errorIndication is None:
            params_from_web = self.parse_inps_and_user_param_content(
                inputs_web_content[0].result(), create_self_attr=True
            )

            params_from_user = []
            if inputs_string:
                params_from_user += self.parse_income_inps(inputs_string)
            if inputs_dict:
                params_from_user += self.parse_income_inps(inputs_dict)
            if kwargs:
                params_from_user += self.parse_income_inps(kwargs)
            logger.debug(params_from_user)
            params_to_set = []
            for data_to_set in params_from_user:
                logger.debug(data_to_set)
                inp, val = data_to_set

                if data_to_set in {
                    (self.CP_RED, self.ACTUATOR_RESET), (self.CP_RED, self.ACTUATOR_OFF), (self.MAN_FLASH, self.ACTUATOR_OFF),
                    (self.CP_FLASH, self.ACTUATOR_RESET), (self.CP_FLASH, self.ACTUATOR_OFF),
                    (self.MAN_FLASH, self.ACTUATOR_RESET), (self.MAN_OFF, self.ACTUATOR_ON), (self.MAN_OFF, self.ACTUATOR_RESET)
                }:
                    set_CP_AUTO = True
                if data_to_set in {
                    (self.CP_RED, self.ACTUATOR_RESET), (self.CP_RED, self.ACTUATOR_OFF),
                    (self.CP_FLASH, self.ACTUATOR_RESET), (self.CP_FLASH, self.ACTUATOR_OFF)
                }:
                    params_to_set.append((params_from_web.get(inp)[0], self.ACTUATOR_OFF))
                    params_to_set.append((params_from_web.get(inp)[0], self.ACTUATOR_RESET))
                    params_to_set.append((params_from_web.get(self.CP_AUTO)[0], self.ACTUATOR_RESET))

                if inp in params_from_web:
                    logger.debug(params_from_web)
                    params_to_set.append((params_from_web.get(inp)[0], val))

                    # params_to_set[params_from_web.get(param)[0]] = val
            if not params_to_set:
                raise ValueError
            # logger.debug(params_to_set)

            set_type = self.SET_INPUTS
            timeout = aiohttp.ClientTimeout(timeout)
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies, timeout=timeout) as session:
                async with asyncio.TaskGroup() as tg:
                    tasks_res = [tg.create_task(self.set_val_to_web(set_type, session, data_params))
                                 for data_params in params_to_set]
                if set_CP_AUTO:
                    await self.set_val_to_web(set_type, session, (params_from_web.get(self.CP_AUTO)[0], self.ACTUATOR_ON))
                    await self.set_val_to_web(set_type, session, (params_from_web.get(self.CP_AUTO)[0], self.ACTUATOR_RESET))

            if any(res.result() != 200 for res in tasks_res):
                errorIndication = EntityJsonResponce.TIMEOUT_ERROR_WEB_REQUEST_MSG.value
                return errorIndication, self.last_set_commands, self

            errorInd, res = await self.get_content_from_web_multiple(
                [self.ROUTE_GET_CURRENT_STATE, self.ROUTE_GET_INPUTS])
            logger.debug(errorInd)
            logger.debug(res)
            return errorIndication, [self.last_set_commands, res], self

    async def set_flash(self, value: str):
        self.put_to_req_data({'protocol': 'http', 'type': 'set', 'request_time': self.set_curr_datetime()})
        self.set_entity[inspect.stack()[0][3]] = value
        return await self.set_val_common(MPP_FL=self.synonyms_red_yellow_dark.get(value))

    async def set_allred(self, value: str):
        self.put_to_req_data({'protocol': 'http', 'type': 'set', 'request_time': self.set_curr_datetime()})
        self.set_entity[inspect.stack()[0][3]] = value
        return await self.set_val_common(CP_RED=self.synonyms_red_yellow_dark.get(value))

    async def reset_all_man_inputs(self):
        self.put_to_req_data({'protocol': 'http', 'type': 'set', 'request_time': self.set_curr_datetime()})
        self.set_entity[inspect.stack()[0][3]] = ''
        return await self.set_val_common(inputs_dict={inp: self.ACTUATOR_RESET_NAME for inp in self.ALL_MPP_INPUTS})

    def parse_income_inps(self, data: str | dict) -> list:
        """
        Формирут список переданных вводов, проверяя на вадидность
        :param data: строка вида 'MPP=ВКЛ;MPP_PH1=ВКЛ'
        :return: список вводов. например: [('MPP', 'ВКЛ'), ('MPP_PH1', 'ВКЛ')]
        """
        filtered_inps = []
        if not data:
            return filtered_inps

        if isinstance(data, str):
            data = [inps.split('=') for inps in data.split(';') if inps]
        elif isinstance(data, dict):
            data = data.items()
        else:
            return filtered_inps

        for inp_data in data:
            if (len(inp_data) != 2 or inp_data[0] not in self.ALLOWED_INPUTS
                    or inp_data[1] not in self.ACTUATOR_VALUES):
                continue
            filtered_inps.append((inp_data[0], self.ACTUATOR_VALUES.get(inp_data[1])))
        return filtered_inps

    def parse_varBinds(self, varBinds: list) -> tuple:
        """
        Метод обрабатывает данные для json responce типа 'set'
        :param varBinds: Список. Состоит из 2 элементов.
                         varBinds[0]: list из команд, отправленных на web. Например:
                         [{'MPP_PH1': 'ВЫКЛ'}, {'MPP_PH2': 'ВКЛ'}]
                         varBinds[1]: различные статусы из web страниц:
                                     {'GET_CURRENT_STATE': ':TITLE;##MENU_001a##\n:SUBTITLE;Moscow: Лит...}
        Пример varBinds:
        [[{'MPP_PH1': 'ВЫКЛ'}, {'MPP_PH2': 'ВКЛ'}], {'GET_CURRENT_STATE': ':TITLE;##MENU_001a##\n:SUBTITLE;Moscow: ...}]
        :return: часть для json с отправленными на веб командами и различными статусами
        """

        sent_commands, data = [], []
        if varBinds[0]:
            sent_commands = varBinds[0] or sent_commands
        if varBinds[1]:
            for d in varBinds[1]:
                if d == self.GET_CURRENT_STATE:
                    basic_curr_state = self.parse_current_mode({d: varBinds[1][d]})[1]
                    data.append(basic_curr_state)
                elif d == self.GET_INPUTS_CONTENT:
                    all_inputs_from_web_page = self.parse_inps_and_user_param_content(varBinds[1][d])
                    curr_state_inps = [f'{inp}: {all_inputs_from_web_page.get(inp)[-1]}' for inp in self.ALL_MPP_INPUTS]
                    data.append({EntityJsonResponce.INPUTS.value: curr_state_inps})
        return sent_commands, data


class PeekSetUserParametersWeb(PeekWebContent):

    def parse_income_user_parameters(self, data: str | dict, params_from_web: dict[str, tuple]) -> list:
        """
        Формирует список переданных параметров программы, проверяя на валидность
        :param data: строка вида 'FIX_TIME=1'
        :return: список параметров программы. например: [('MPP', 'ВКЛ'), ('MPP_PH1', 'ВКЛ')]
        """

        filtered_params = []
        if not data:
            return filtered_params

        if isinstance(data, str):
            data = [inps.split('=') for inps in data.split(';') if inps]
        elif isinstance(data, dict):
            data = data.items()
        else:
            return filtered_params

        for up_data in data:
            if len(up_data) != 2:
                continue
            name, val = up_data
            try:
                if int(val) > int(params_from_web.get(name)[-1]):
                    continue
            except ValueError:
                continue
            except TypeError:
                continue
            filtered_params.append((up_data[0], up_data[1]))
        return filtered_params

    async def set_user_parameters(
            self, timeout=3, params_string: str = None, params_dict: dict[str, str] = None, **kwargs
    ):
        self.put_to_req_data({'protocol': 'http', 'type': 'set', 'request_time': self.set_curr_datetime()})
        self.set_entity[inspect.stack()[0][3]] = params_string or params_dict or kwargs

        errorIndication, user_params = await self.get_content_from_web_multiple([self.ROUTE_GET_USER_PARAMETERS])
        if errorIndication is None:
            params_from_web = self.parse_inps_and_user_param_content(
                user_params[0].result(), create_self_attr=True
            )
            logger.debug(params_from_web)
            logger.debug(self.last_read_parameters)
            params_from_user = []
            if params_string:
                params_from_user += self.parse_income_user_parameters(params_string, params_from_web)
            if params_dict:
                params_from_user += self.parse_income_user_parameters(params_dict, params_from_web)
            if kwargs:
                params_from_user += self.parse_income_user_parameters(kwargs, params_from_web)
            logger.debug(params_from_user)

            if not params_from_user:
                errorIndication = EntityJsonResponce.BAD_DATA_SET_REQ.value
                return errorIndication, self.last_set_commands, self

            params_to_set = [
                (params_from_web.get(name)[0], val) for name, val in params_from_user
            ]
            logger.debug(params_to_set)
            timeout = aiohttp.ClientTimeout(timeout)
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies, timeout=timeout) as session:
                async with asyncio.TaskGroup() as tg:
                    res = [
                        tg.create_task(self.set_val_to_web(self.SET_USER_PARAMETERS, session, data))
                        for data in params_to_set
                    ]

            errorIndication = self.has_error_in_taskgroup(res)
            if errorIndication is not None:
                return errorIndication, self.last_set_commands, self
            errorInd, res = await self.get_content_from_web_multiple(
                [self.ROUTE_GET_CURRENT_STATE, self.ROUTE_GET_USER_PARAMETERS])
            logger.debug(errorInd)
            logger.debug(res)
            return errorIndication, [self.last_set_commands, res], self

    def parse_varBinds(self, varBinds: list) -> tuple:
        """
        Метод обрабатывает данные для json responce типа 'set'
        :param varBinds: Список. Состоит из 2 элементов.
                         varBinds[0]: list из команд, отправленных на web. Например:
                         [{'UTC_ON': '0'}}]
                         varBinds[1]: различные статусы из web страниц:
                                     {'GET_CURRENT_STATE': ':TITLE;##MENU_001a##\n:SUBTITLE;Moscow: Лит...}
        Пример varBinds:
        [[{'UTC_ON': '0'}], {'GET_CURRENT_STATE': ':TITLE;##MENU_001a##\n:SUBTITLE;Moscow: ...},
        {'GET_USER_PARAMETERS': ':TITLE;##CELL_6710##\n:TFT_NAVBAR;0\n:TFT_EDIT;1\n:MI}]
        :return: часть для json с отправленными на веб командами и различными статусами
        """

        sent_commands, data = [], []
        logger.debug(varBinds[0])
        if varBinds[0]:
            sent_commands = varBinds[0] or sent_commands
        if varBinds[1]:
            for d in varBinds[1]:
                if d == self.GET_CURRENT_STATE:
                    basic_curr_state = self.parse_current_mode({d: varBinds[1][d]})[1]
                    data.append(basic_curr_state)
                elif d == self.GET_USER_PARAMETERS_CONTENT:
                    user_parameters = self.user_parameters_to_list_for_json(varBinds[1][d])
                    data.append({EntityJsonResponce.USER_PARAMETERS.value: user_parameters})
        logger.debug([sent_commands])
        logger.debug(data)
        return sent_commands, data


class GetDifferentStatesFromWeb(PeekWebContent):

    async def get_request(self, **kwargs) -> tuple[str | None, list[asyncio.Task], PeekWebContent]:
        """
        Метод получает веб контент страницы по маршрутам из routes
        :param kwargs:
        :return: кортеж вида: None(если нет ошибки), list с завершенными задачами, объект
        """
        self.put_to_get_entity('get_states')
        self.put_to_req_data({'protocol': 'http', 'type': 'get', 'request_time': self.set_curr_datetime()})
        routes = [
            self.routes_url.get(self.GET_CURRENT_STATE), self.routes_url.get(self.GET_INPUTS_CONTENT),
            self.routes_url.get(self.GET_USER_PARAMETERS_CONTENT)
        ]
        errorIndication, content = await self.get_content_from_web_multiple(routes)
        return errorIndication, content, self

    def parse_varBinds(self, varBinds: dict):
        """
        Обрабатывает данные для json responce
        :param varBinds: словарь с распарсенными данными с веб страницы, например:
        {'GET_CURRENT_STATE': ':TITLE;##MENU_00..., 'GET_INPUTS': ':TITLE;##CELL_1020##\n:TFT_NAVBAR;3\n:TFT_ED...}
        :return: часть для json responce
        """

        varBinds, basic_curr_mode = self.parse_current_mode(varBinds)
        inps = self.inputs_to_list_for_json(varBinds.snmp_get(self.GET_INPUTS_CONTENT))
        user_parameters = self.user_parameters_to_list_for_json(varBinds.snmp_get(self.GET_USER_PARAMETERS_CONTENT))
        part_of_json = {}
        part_of_json |= basic_curr_mode
        part_of_json[EntityJsonResponce.INPUTS.value] = inps
        part_of_json[EntityJsonResponce.USER_PARAMETERS.value] = user_parameters
        logger.debug(part_of_json)
        return part_of_json


class SwarcoWebBase(BaseCommon):
    ROUTE_MAIN = os.getenv('ROUTE_MAIN')
    ROUTE_LOGOUT = os.getenv('ROUTE_LOGOUT')
    ROUTE_DISPLAY = os.getenv('ROUTE_DISPLAY')
    ROUTE_DATA = os.getenv('ROUTE_DATA')
    ROUTE_RESET_SESSIONS = os.getenv('ROUTE_RESET_SESSIONS')

    ENCODING_WEB = os.getenv('ENCODING_WEB')

    headers = {
        'User-Agent': os.getenv('user_agent')
    }

    def __init__(self, ip_adress: str, host_id: str = None):
        super().__init__(ip_adress, host_id)
        self.ip_adress = ip_adress
        self.host_id = host_id
        self.set_controller_type()


class SwarcoWebLogin(SwarcoWebBase):
    payload = {
        os.getenv('k1_swarco_web'): os.getenv('k2_swarco_web'),
        os.getenv('k3_swarco_web'): os.getenv('k4_swarco_web'),
        os.getenv('k5_swarco_web'): os.getenv('k6_swarco_web'),
        os.getenv('k7_swarco_web'): os.getenv('k8_swarco_web'),
    }

    async def login(self, session: aiohttp.ClientSession):
        """
        Метод логинится в веб сесиию
        :param session: session aiohttp.ClientSession
        :param timeout: таймаут на сессию
        :return: обьект сессии для дальнейших запросов
        """
        url = f'http://{self.ip_adress}{self.ROUTE_MAIN}'
        async with session.post(url, headers=self.headers, data=self.payload) as s:
            r = await s.text()
            logger.debug(r)
            session.cookie_jar.update_cookies(s.cookies)
            return session


class SwarcoWebContent(SwarcoWebLogin):

    async def get_content_from_web(self, route_type: str, timeout=2) -> tuple:
        """
        Метод забирает контент с веб страницы
        :param route_type: маршрут к необходимой странице
        :param timeout: таймаут сессии
        :return: errorIndication, content
        """

        errorIndication = content = None
        try:
            timeout = aiohttp.ClientTimeout(timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                session = await self.login(session)
                async with session.get(f'http://{self.ip_adress}{route_type}') as s:
                    content = await s.text(encoding=self.ENCODING_WEB)
                    logger.debug(content)
                    if s.status != 200:
                        raise TypeError(EntityJsonResponce.TYPE_CONTROLLER_ERROR_MSG.value)
                if 'msg:"key sent"' in content:
                    async with session.get(f'http://{self.ip_adress}{self.ROUTE_DATA}') as s:
                        content = await s.text(encoding=self.ENCODING_WEB)
                        # logger.debug(content)
                        if s.status != 200:
                            raise TypeError(EntityJsonResponce.TYPE_CONTROLLER_ERROR_MSG.value)
                async with session.get(f'http://{self.ip_adress}{self.ROUTE_LOGOUT}') as s:
                    logout = await s.read()
                    if s.status != 200:
                        raise TypeError(EntityJsonResponce.TYPE_CONTROLLER_ERROR_MSG.value)
                    errorIndication = None
        except aiohttp.client_exceptions.ClientConnectorError:
            errorIndication, content = EntityJsonResponce.NETWORK_CONNECTION_ERROR.value, []
        except asyncio.TimeoutError:
            errorIndication, content = EntityJsonResponce.TIMEOUT_ERROR_WEB_REQUEST_MSG.value, []
        except TypeError:
            errorIndication, content = EntityJsonResponce.TYPE_CONTROLLER_ERROR_MSG.value, []
        finally:
            return errorIndication, content


    def parse_current_mode(self, content: str) -> tuple:
        """
        Метод парсит данные, полученные с веб страницы для определения переменных текущего состояния ДК
        :param content: контент с веб страницы
        :return: кортеж, где первый элемент пустой список, второй элемент -> dict(часть json из ключа basic)
        """
        if content.startswith('{ "CFG":'):
            processed_content = self.parse_content_6_94_8(content)
        else:
            processed_content = self.parse_content_6_94_2(content)
            # processed_content = [line.split(': ', maxsplit=1)[-1] for line in content.splitlines() if line]
        logger.debug(processed_content)

        line3 = processed_content[2].split()
        curr_plan = curr_mode = curr_cyc = None
        if len(line3) == 3:
            curr_plan, curr_mode, curr_cyc = line3
        elif len(line3) == 2:
            curr_plan, curr_mode = line3
        curr_stage, curr_stage_time = processed_content[3].split()[-2:]
        curr_system_time = processed_content[1].split()[-1]
        button_vals = self.parse_button_vals(processed_content[-1])
        processed_content.append(button_vals)
        logger.debug(processed_content)
        basic_curr_state = {
            EntityJsonResponce.BASIC_STATE.value: {
                EntityJsonResponce.CURRENT_MODE.value: curr_mode,
                EntityJsonResponce.CURRENT_STAGE.value: curr_stage,
                EntityJsonResponce.CURRENT_STAGE_TIME.value: curr_stage_time,
                EntityJsonResponce.CURRENT_CYC_TIMME.value: curr_cyc,
                EntityJsonResponce.CURRENT_PLAN.value: curr_plan,
                EntityJsonResponce.CURRENT_SYSTEM_TIME.value: curr_system_time,
                EntityJsonResponce.CURRENT_STATE_BUTTONS.value: button_vals,
                EntityJsonResponce.WEB_CONTENT_STATE.value: processed_content
            }
        }
        return [], basic_curr_state

    def parse_button_vals(self, string_vals: str) -> str:
        matches = {
            '0': 'ON',
            '1': 'OFF',
            '2': 'ALL_RED',
            '3': 'FLASH',
            '4': 'MAN_CTRL_ON',
            '5': 'MAN_CTRL_SHIFT',
            '6': 'FIXED_CTRL',
            '7': 'LOCAL_CTRL',
        }
        processed_string, string_vals = '', string_vals.replace(" ", '')

        if string_vals[0] == '1':
            processed_string += f'SIGNALS={matches.get("0")}'
        elif string_vals[1] == '1':
            processed_string += f'SIGNALS={matches.get("1")}'
        if string_vals[2] == '1':
            processed_string += f' | {matches.get("2")}=ON'
        elif string_vals[3] == '1':
            processed_string += f' | {matches.get("3")}=ON'
        if string_vals[6] == '1':
            processed_string += f' | {matches.get("6")}=ON'
        if string_vals[7] == '1':
            processed_string += f' | {matches.get("7")}=ON'
        return processed_string

    def parse_content_6_94_8(self, content: str) -> list:
        """
        Парсер контента, полученного с веб для прошивки 6.94.8
        :param content:
        :return:
        """

        content = content.split('VD:')[-1][:-1].encode(encoding=self.ENCODING_WEB).decode()
        logger.debug(content)
        content_to_dict = ast.literal_eval(content)
        logger.debug(content_to_dict)

        if content_to_dict.snmp_get('virtual_display').snmp_get('display2'):
            content_to_list = content_to_dict.snmp_get('virtual_display').snmp_get('display2')
        elif content_to_dict.snmp_get('virtual_display').snmp_get('display1'):
            content_to_list = content_to_dict.snmp_get('virtual_display').snmp_get('display1')
        else:
            raise ValueError
        # logger.debug(content_to_list)
        # logger.debug(type(content_to_list))

        content_to_list.append(
            " ".join([str(v) for v in content_to_dict.snmp_get('virtual_display').snmp_get('signals')])
        )
        return content_to_list

    def parse_content_6_94_2(self, content: str) -> list:
        return [line.split(': ', maxsplit=1)[-1] for line in content.splitlines() if line]

    def get_current_mode(self, content: str) -> tuple:
        """
        Метод получает распарсенные данные для json responce о текущем состоянии ДК
        :param content:
        :return: распарсенные данные о текущем состоянии ДК
        """

        return self.parse_current_mode(content)


class SwarcoGetModeWeb(SwarcoWebContent):

    async def get_request(self, get_mode: bool = True, timeout=1) -> tuple:
        """
        Метод запроса контента web страницы получения текущего состояния ДК
        :param get_mode:
        :param timeout:
        :return tuple: (errorIndication, varBinds)
        """
        if get_mode:
            self.put_to_get_entity('get_mode')
            self.put_to_req_data({'protocol': 'http', 'type': 'get', 'request_time': self.set_curr_datetime()})

        errorIndication, content = await self.get_content_from_web(route_type=self.ROUTE_DISPLAY, timeout=timeout)
        self.errorIndication, self.varBinds = errorIndication, content
        # logger.debug(errorIndication)
        # logger.debug(content)
        return errorIndication, content, self


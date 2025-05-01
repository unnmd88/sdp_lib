from collections.abc import KeysView
import os

from pysnmp.hlapi.v3arch.asyncio import *

from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.utils_common import check_is_ipv4



class Host:
    """
    Базовый класс для любого хоста.
    """
    def __init__(self, ip_v4: str, host_id=None):
        self.ip_v4 = ip_v4
        self.host_id = host_id
        # self.scn = scn
        # self.query_data = []

    def __repr__(self):
        return (
            f'ip_v4: {self.ip_v4}\n'
            f'host_id: {self.host_id}\n'
        )

    def __setattr__(self, key, value):
        if key == 'ip_v4':
            if check_is_ipv4(value):
                self.__dict__[key] = value
            else:
                raise ValueError(f'Значение < self.ipv4 > должно быть валидным ipv4 адресом: {value}')

        elif key == 'scn':
            if value is None or len(value) <= 10:
                self.__dict__[key] = value
            else:
                raise ValueError('Значение < self.scn > не должно превышать 10 символов ')
        else:
            self.__dict__[key] = value


class SnmpHost(Host):
    def __init__(self, ip_v4: str, host_id: str = None, scn: str = None):
        Host.__init__(self, ip_v4, host_id)
        self.scn = scn
        self.community_r, self.community_w = self.get_community()

    def get_community(self) -> tuple[str, str]:
        raise NotImplemented()


class BaseSnmp(SnmpHost):
    """
    Интерфейс отправки snmp запросов.
    """
    snmp_engine = SnmpEngine()

    @classmethod
    async def get_request_base(
            cls,
            ip_v4: str,
            community: str,
            oids: list[str],
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
        error_indication, error_status, error_index, var_binds = await get_cmd(
            cls.snmp_engine,
            CommunityData(community),
            await UdpTransportTarget.create((ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return error_indication, var_binds

    async def get_request(
            self,
            oids: list[str | Oids] | KeysView[str | Oids],
            timeout: float = 0.2,
            retries: int = 0
    ) -> tuple:
        """
        Метод get запросов по протоколу snmp.
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
        error_indication, error_status, error_index, var_binds = await get_cmd(
            BaseSnmp.snmp_engine,
            CommunityData(self.community_r),
            await UdpTransportTarget.create((self.ip_v4, 161), timeout=timeout, retries=retries),
            ContextData(),
            *[ObjectType(ObjectIdentity(oid)) for oid in oids]
        )
        return error_indication, var_binds


class BaseSTCIP(BaseSnmp):

    def get_community(self) -> tuple[str, str]:
        return os.getenv('communitySTCIP_r'), os.getenv('communitySTCIP_w')

    async def get_multiple(self, oids: list[str | Oids]):
        print('я в функции get_multiple')
        res = await self.get_request(oids=oids)
        print('я в функции get_multiple перед return')
        return res


class SwarcoSTCIP(BaseSTCIP):

    status_equipment = {
        '0': 'noInformation',
        '1': str(FieldsNames.three_light),
        '2': str(FieldsNames.power_up),
        '3': str(FieldsNames.dark),
        '4': str(FieldsNames.flash),
        '6': str(FieldsNames.all_red),
    }

    plan_source = {
        '1': 'trafficActuatedPlanSelectionCommand',
        '2': 'currentTrafficSituationCentral',
        '3': 'controlBlockOrInput',
        '4': 'manuallyFromWorkstation',
        '5': 'emergencyRoute',
        '6': 'currentTrafficSituation',
        '7': 'calendarClock',
        '8': 'controlBlockInLocal',
        '9': 'forcedByParameterBP40',
        '10': 'startUpPlan',
        '11': 'localPlan',
        '12': 'manualControlPlan',
    }

    def convert_val_to_num_stage_get_req(self, val: str) -> int | None:
        """
        Конвертирует значение из oid фазы в номер фазы из get заспроа
        :param val: значение, которое будет сконвертировано в десятичный номер фазы.
        :return: номер фазы в десятичном представлении
        """

        values = {'2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0}
        return values.get(val)

    def convert_val_to_num_stage_set_req(self, val: str) -> int | None:
        """
        Конвертирует номер фазы в значение для установки в oid фазы
        :param val: номер фазы, который будет сконвертирован в соответствующее значение
        :return: Значение фазы, которое будет установлено.
        """

        values = {'1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 1, 'ЛОКАЛ': 0, '0': 0}
        return values.get(val)

    def get_plan_source(self, value: str) -> str:
        return value

    def get_status(self, value: str, status_equipment: dict[str, str]) -> str:
        return status_equipment.get(value)

    def get_fixed_time_status(self, value: str) -> str:
        return value

    def get_plan(self, value: str) -> str:
        return value

    def get_num_det(self, value: str) -> str:
        return value

    def get_soft_flags_status(self, octet_string: str, start: int = 179, stop: int = 181, ) -> str:
        return octet_string[start: stop]

    def get_current_mode(self, response_data: dict[str, str], mode=None) -> str | None:

        if response_data.get(FieldsNames.curr_plan) == '16' and response_data.get(FieldsNames.plan_source) == '3':
            mode = str(NamesMode.CENTRAL)
        elif (
            response_data.get(FieldsNames.fixed_time_status) == '1'
            or '1' in response_data.get(FieldsNames.status_soft_flag180_181)
            or response_data.get(FieldsNames.num_detectors) == '0'
        ):
            mode = str(NamesMode.FT)
        elif (
            response_data.get(FieldsNames.fixed_time_status) == '0'
            and '1' not in response_data.get(FieldsNames.status_soft_flag180_181)
            and int(response_data.get(FieldsNames.num_detectors)) > 0
        ):
            mode = str(NamesMode.VA)
        elif response_data.get(FieldsNames.curr_plan) == '15' and response_data.get(FieldsNames.plan_source) == '3':
            mode = str(NamesMode.MANUAL)
        elif response_data.get(FieldsNames.curr_plan) == '13' and response_data.get(FieldsNames.plan_source) == '3':
            mode = str(NamesMode.SYNC)
        return mode

    def get_oid_val(self, var_binds: tuple[ObjectType]):
        return [x.prettyPrint() for x in var_binds]

    async def get_stage(self):
        error_indication, var_binds = await self.get_request(
            oids=[Oids.swarcoUTCTrafftechPhaseStatus]
        )
        if error_indication is None:
            # print(f'ip: {self.ip_v4}\nstage: {var_binds[0][1]}')
            print(f'ip: {self.ip_v4}\nstage: {self.convert_val_to_num_stage_get_req(str(var_binds[0][1]))}')
            return self.convert_val_to_num_stage_get_req(var_binds)
        return error_indication

        # return error_indication, [(str(x[0]), str(x[1])) for x in var_binds]

    def parse_raw_data_for_basic_current_state(self, raw_data: tuple):
        # print(f'raw_data:: {raw_data}')
        # print(f'len(raw_data):: {len(raw_data)}')
        # print(f'raw_data[0]:: {raw_data[0]}')
        print([(x[0].prettyPrint(), x[1].prettyPrint()) for x in raw_data])
        print([(str(x[0]), str(x[1])) for x in raw_data])

        for varBind in raw_data:
            # print(f'varBind:: {varBind}')
            # print(f'type(varBind):: {type(varBind)}')

            print(" <><> ".join([x.prettyPrint() for x in varBind]))
            print([x.prettyPrint() for x in varBind])


class SwarcoCurrentStatesSTCIP(SwarcoSTCIP):

    state_base: dict = {
        Oids.swarcoUTCTrafftechFixedTimeStatus: (FieldsNames.fixed_time_status, SwarcoSTCIP.get_fixed_time_status),
        Oids.swarcoUTCTrafftechPlanSource: (FieldsNames.plan_source, SwarcoSTCIP.get_plan_source),
        Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, SwarcoSTCIP.get_status),
        Oids.swarcoUTCTrafftechPhaseStatus: (FieldsNames.curr_stage, SwarcoSTCIP.convert_val_to_num_stage_get_req),
        Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, SwarcoSTCIP.get_plan),
        Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, SwarcoSTCIP.get_num_det),
        Oids.swarcoSoftIOStatus: (FieldsNames.status_soft_flag180_181, SwarcoSTCIP.get_soft_flags_status)
    }

    def parse_response(
            self,
            response: [tuple[ObjectIdentity, OctetString | Gauge32 | Integer | Unsigned32]]
    ) -> dict[str, str]:
        # print(f'response: {response}')
        resp = {}
        # for oid, val in ((str(x[0]), str(x[1])) for x in response):
        for oid, val in response:
            oid, val = str(oid), str(val)
            field_name, fn = SwarcoCurrentStatesSTCIP.state_base.get(oid)
            resp[str(field_name)] = fn(self, val)
        resp[str(FieldsNames.curr_mode)] = self.get_current_mode(resp)
        print(f'resp: {resp}')
        return resp

    async def get_data_for_basic_current_state(self):
        error_indication, var_binds = await self.get_request(
            oids=SwarcoCurrentStatesSTCIP.state_base.keys()
        )

        return error_indication, self.parse_response(var_binds)



import abc
import asyncio
import pprint
import sys
import time

from pysnmp.entity.engine import SnmpEngine
from pysnmp.proto import rfc1905
from pysnmp.proto.rfc1902 import (
    Unsigned32,
    Integer,
    OctetString,
    Integer32
)
from pysnmp.smi.rfc1902 import (
    ObjectType,
    ObjectIdentity
)
from sdp_lib.management_controllers.snmp import (
    oids,
    snmp_requests,
    snmp_config
)
from sdp_lib.management_controllers.snmp._types import (
    T_Oids,
    T_Varbinds
)
from sdp_lib.management_controllers.snmp.oids import (
    Oids,
    oids_scn_required
)
from sdp_lib.management_controllers.snmp.snmp_utils import (
    convert_chars_string_to_ascii_string,
    convert_val_to_num_stage_set_req_ug405,
    wrap_oid_by_object_type
)


ug405_stage_values = convert_val_to_num_stage_set_req_ug405(128)

swarco_stcip_set_stage_varbinds = {
    num_stage: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(num_stage + 1))
    for num_stage in range(1, 8)
} | {8: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(1)),
     0: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(0))}

potok_stcip_set_stage_varbinds = {
    num_stage: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(num_stage + 1))
    for num_stage in range(1, 129)
} | {0: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(0))}


class Varbinds:

    _oids_state: T_Oids
    _varbinds_get_state: T_Varbinds | dict[str, T_Varbinds]

    def __init__(self):
        # self._oids_state = oids_state
        # self._varbinds_get_state = self._build_varbinds_for_get_state()
        self._build_varbinds_for_get_state()

    @abc.abstractmethod
    def _build_varbinds_for_get_state(self) -> T_Varbinds | dict[str, T_Varbinds]:
        ...

    @classmethod
    def get_varbinds_current_states(cls, *args, **kwargs):
        return cls._varbinds_get_state


class VarbindsStcip(Varbinds):

    _varbinds_set_stage: dict[int, T_Varbinds]

    @classmethod
    def _build_varbinds_for_get_state(cls):
        cls._varbinds_get_state = [wrap_oid_by_object_type(oid) for oid in cls._oids_state]

    @classmethod
    def get_varbinds_set_stage(cls, num_stage) -> list[ObjectType]:
        return [cls._varbinds_set_stage.get(num_stage)]

    # def _build_varbinds_for_set_stage(self) -> dict[int, ObjectType]:
    #     raise NotImplementedError()

    # @classmethod
    # def get_varbinds_set_stage(cls, num_stage) -> list[ObjectType]:
    #     return [cls._varbinds_set_stage.get(num_stage)]


class VarbindsSwarco(VarbindsStcip):

    _oids_state = oids.oids_state_swarco
    _varbinds_set_stage = swarco_stcip_set_stage_varbinds

    # @classmethod
    # def _build_varbinds_for_set_stage(cls) -> dict[int, ObjectType]:
    #     return {
    #         num_stage: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(num_stage + 1))
    #         for num_stage in range(1, 8)
    #     } | {8: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, 1),
    #          0: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, 0)}


class VarbindsPotokS(VarbindsStcip):

    _oids_state = oids.oids_state_potok_s
    _varbinds_set_stage = potok_stcip_set_stage_varbinds

    # def _build_varbinds_for_set_stage(self) -> dict[int, ObjectType]:
    #     return {
    #         num_stage: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(num_stage + 1))
    #         for num_stage in range(1, 129)
    #     } | {0: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, 0)}


class VarbindsUg405(Varbinds):

    max_scn = 9999
    num_CO_prefix = 'CO'

    operation_mode_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode)
    operation_mode1_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode, Integer32(1))
    operation_mode2_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode, Integer32(2))
    operation_mode3_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode, Integer32(3))

    site_id_varbind = wrap_oid_by_object_type(Oids.utcReplySiteID)

    hex_vals128 = {i: OctetString(hexValue=ug405_stage_values.get(str(i))) for i in range(1, 129)}

    integer_vals128 = {i: Integer32(i) for i in range(129)}
    integer32_val1 = Integer32(1)
    integer32_val2 = Integer32(2)
    integer32_val3 = Integer32(3)

    def add_scn_to_oids(
            self,
            scn: str,
            oids: T_Oids,
    ) -> list[Oids | str | ObjectType]:

        return [
            f'{oid}{scn}' if oid in oids.oids_scn_required else oid
            for oid in oids
        ]

    @classmethod
    def add_scn_to_oids_and_wrap_by_object_identity(
            cls,
            scn: str,
            oids: T_Oids,
    ):
        return [
            ObjectType(ObjectIdentity(f'{oid}{scn}')) if oid in oids_scn_required
            else ObjectType(ObjectIdentity(oid))
            for oid in oids
        ]

    @classmethod
    def _build_varbinds_for_get_state(cls):
        start_time = time.time()

        cls._varbinds_get_state = {}
        for i in range(1, cls.max_scn):
            scn = convert_chars_string_to_ascii_string(f'{cls.num_CO_prefix}{str(i)}')
            curr_states_object_type = cls.add_scn_to_oids_and_wrap_by_object_identity(
                scn, cls._oids_state
            )
            cls._varbinds_get_state[scn] = curr_states_object_type
        print(f'FinS: {time.time() - start_time}')

    @classmethod
    def _build_varbinds_for_get_state_and_add_to_varbinds_attr(cls, scn_as_ascii):
        curr_states_varbinds = cls.add_scn_to_oids_and_wrap_by_object_identity(
            scn_as_ascii, cls._oids_state
        )
        cls._varbinds_get_state[scn_as_ascii] = curr_states_varbinds
        return curr_states_varbinds

    @classmethod
    def get_varbinds_current_states(cls, scn_as_ascii: str) -> T_Varbinds:
        return (cls._varbinds_get_state.get(scn_as_ascii)
                or cls._build_varbinds_for_get_state_and_add_to_varbinds_attr(scn_as_ascii)
            )

    @classmethod
    def get_varbinds_set_stage(
            cls,
            scn_as_ascii: str,
            num_stage: int
    ) -> T_Varbinds:
        if 0 < num_stage < 129:
            return (
                cls.operation_mode3_varbind,
                wrap_oid_by_object_type(f'{str(Oids.utcControlTO)}{scn_as_ascii}', cls.integer32_val1),
                wrap_oid_by_object_type(f'{Oids.utcControlFn}{scn_as_ascii}', cls.hex_vals128.get(num_stage)),
                # wrap_oid_by_object_type(f'{Oids.utcControlFn}{scn_as_ascii}', OctetString(hexValue='1'))
            )
        return (cls.operation_mode1_varbind, )

    @classmethod
    def get_operation_mode_varbinds(cls, op_mode_val: int) -> ObjectType:
        if op_mode_val == 3:
            return cls.operation_mode3_varbind
        if op_mode_val == 2:
            return cls.operation_mode2_varbind
        return cls.operation_mode1_varbind


class VarbindsPotokP(VarbindsUg405):

    _oids_state = oids.oids_state_potok_p


class VarbindsPeek(VarbindsUg405):
    _oids_state = oids.oids_state_peek_ug405


# Singleton instances
potok_ug405_varbinds = VarbindsPotokP()
potok_stcip_varbinds = VarbindsPotokS()
swarco_stcip_varbinds = VarbindsSwarco()
peek_ug405_varbinds = VarbindsPeek()


class AbstractVarbindsWrappersByScn:

    _ug405_varbinds: potok_ug405_varbinds

    def __init__(self, scn_as_ascii: str = None):
        self._scn_as_ascii = scn_as_ascii

    @classmethod
    def get_varbinds_current_states_by_scn(
            cls,
            scn_as_ascii: str
    ):
        return cls._ug405_varbinds.get_varbinds_current_states(scn_as_ascii)

    @classmethod
    def get_varbinds_set_stage_by_scn(
            cls,
            scn_as_ascii: str,
            value: int
    ):
        return cls._ug405_varbinds.get_varbinds_set_stage(scn_as_ascii, value)

    def get_varbinds_current_states(self):
        return self._ug405_varbinds.get_varbinds_current_states(self._scn_as_ascii)

    def get_varbinds_set_stage(self, value: int) -> T_Varbinds:
        return self._ug405_varbinds.get_varbinds_set_stage(self._scn_as_ascii, value)

    @property
    def ug405_varbinds(self) -> VarbindsUg405:
        return self._ug405_varbinds

    @property
    def scn_as_ascii(self):
        return self._scn_as_ascii

    @scn_as_ascii.setter
    def scn_as_ascii(self, value: str):
        if not isinstance(value, str):
            raise ValueError(f"Уставливое значение 'scn_as_ascii' должно быть типа str")
        if value.count('.') < 2:
            if not isinstance(value, str):
                raise ValueError(f"Проверьте корректность устанавливаемого значения 'scn_as_ascii'.")
        self._scn_as_ascii = value


class WrapperVarbindsByScnPotokP(AbstractVarbindsWrappersByScn):

    _ug405_varbinds = potok_ug405_varbinds


def build_test_obj():
    p = VarbindsPotokP()
    scn155 = convert_chars_string_to_ascii_string('CO155')

    # vb = p.get_varbinds_get_state_by_scn(scn_as_ascii=scn155)
    # print(vb)
    print(f'Volume: {sys.getsizeof(p._varbinds_get_state)}')
    print(f'Volume 2 : {sys.getsizeof(list(p._varbinds_get_state.values()))}')
    print(f'Volume 1 el: {sys.getsizeof(p._varbinds_get_state.get(scn155))}')


async def main():


    r_sender = snmp_requests.SnmpRequests(
        ip='10.179.8.105',
        community_r=host_data.swarco_stcip.community_r,
        community_w=host_data.swarco_stcip.community_w,
        engine=SnmpEngine()
    )

    r_sender = snmp_requests.SnmpRequests(
        # ip='10.179.56.105',
        ip='10.179.69.65',
        community_r=host_data.potok_p.community_r,
        community_w=host_data.potok_p.community_w,
        engine=SnmpEngine()
    )

    r_sender = snmp_requests.SnmpRequests(
        # ip='10.179.56.105',
        ip='10.179.69.65',
        community_r=host_data.potok_p.community_r,
        community_w=host_data.potok_p.community_w,
        engine=SnmpEngine()
    )

    r_sender = snmp_requests.SnmpRequests(
        # ip='10.179.56.105',
        ip='10.179.68.177',
        community_r=host_data.potok_s.community_r,
        community_w=host_data.potok_s.community_w,
        engine=SnmpEngine()
    )

    res = await r_sender.snmp_get(potok_stcip_varbinds.get_varbinds_current_states())

    print(res)

    potok_stcip_varbinds.parse_response(res[3])

if __name__ == '__main__':
    asyncio.run(main())
    # res = {}
    # for i in range(1, 1000)
    #     res[i] = 0
    start_time = time.time()
    # build_test_obj()






import logging
import math
from collections.abc import Iterable
from typing import Type

from pysnmp.proto import rfc1905
from pysnmp.proto.rfc1902 import (
    Unsigned32,
    OctetString,
    Integer32
)
from pysnmp.smi.rfc1902 import (
    ObjectType,
    ObjectIdentity
)

from sdp_lib.constants import swarco_itc2, potok
from sdp_lib.management_controllers.snmp import oids
from sdp_lib.management_controllers.snmp.user_types import (
    T_Oids,
    T_Varbinds,
    T_Varbind,
    Oid_Value
)
from sdp_lib.management_controllers.snmp.oids import (
    Oids,
    oids_scn_required
)
from sdp_lib import logging_config


logger = logging.getLogger(__name__)


def convert_val_to_num_stage_set_req_ug405(
        max_stage: int
) -> dict:
    stg_mask = ['01', '02', '04', '08', '10', '20', '40', '80']
    return {
        str(k): v for k, v in enumerate((f'{i}{j * "00"}' for j in range(max_stage // 8) for i in stg_mask), 1)
    }


def wrap_oid_by_object_type(
        oid: Oids | str,
        val: Oid_Value = rfc1905.unSpecified
) -> T_Varbind:
    return ObjectType(ObjectIdentity(oid), val)


def convert_chars_string_to_ascii_string(
        scn_as_chars: str
) -> str:
    """
    Генерирует SCN.
    :param  scn_as_chars: символы строки, которые необходимо конвертировать, например: CO3995.
    :return -> возвращет scn виде строки ascii, например .1.6.67.79.51.57.57.53.
    """
    return f'.1.{str(len(scn_as_chars))}.{".".join([str(ord(c)) for c in scn_as_chars])}'


def create_varbinds(
        oids: Iterable[T_Oids],
        container: Type[list | tuple] = list
) -> Iterable[T_Varbind]:
    """
    Оборачивает каждый оид из oids в класс ObjectIdentity.
    :param oids: Итерируемые объект, элементы которого представлены T_Oids.
    :param container: Тип(класс) контейнера, в котором будет возвращён результат(list, tuple, set...).
    :return: Итерируемый объект, каждый элемент которого будет обёрнут классом ObjectIdentity.
    """
    return container(wrap_oid_by_object_type(oid) for oid in oids)


def add_scn_to_oids(
        scn_as_ascii: str,
        oids: [T_Oids],
        wrap_oids_by_object_type=False,
        container: Type[list | tuple] = list
) -> T_Oids | T_Varbinds:
    """
    Добавляет scn_as_ascii к каждому элементу из итерируемого объекта oids.
    :param scn_as_ascii: scn в виде строки. Пример: .1.6.67.79.51.57.57.53
    :param oids: Итерируемый объект, элементы которого представлены T_Oids.
    :param wrap_oids_by_object_type: Если True, то каждый оид + scn будет обёрнут классом ObjectIdentity.
    :param container: Тип(класс) контейнера, в котором будет возвращён результат(list, tuple, set...).
    :return: Итерируемый объект, каждый элемент которого будет обёрнут классом ObjectIdentity.
    """
    if not wrap_oids_by_object_type:
        return container(oid + scn_as_ascii if oid in oids_scn_required else oid for oid in oids)

    return container(
        ObjectType(ObjectIdentity(f'{oid}{scn_as_ascii}')) if oid in oids_scn_required
        else ObjectType(ObjectIdentity(oid))
        for oid in oids
    )


def remove_scn_from_oid(oid: str, scn_as_ascii_string) -> str:
    return oid.replace(scn_as_ascii_string, '')


def create_varbinds_get_state_with_scn(
        get_state_oids_pattern: T_Oids,
        prefix: str = 'CO',
        num_co_min: int = 1,
        num_co_max: int = 9999
) -> dict[str, Iterable[T_Varbinds]]:
    varbinds_get_state = {}
    for num_co in range(num_co_min, num_co_max + 1):
        scn = convert_chars_string_to_ascii_string(f'{prefix}{str(num_co)}')
        varbinds_get_state[scn] = add_scn_to_oids(
            scn,
            get_state_oids_pattern,
            wrap_oids_by_object_type=True
        )
    return varbinds_get_state

def convert_val_as_hex_to_decimal(val: str) -> int | None:
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
        logger.error(f'Значение val: {val}')
        raise


def create_stcip_set_stage_varbinds(
    max_stage: int,
    user_vals: dict[int, int] = None
) -> dict[int, T_Varbind]:
    """
    Формирует словарь с varbinds для утсановки фазы.
    :param max_stage: Максимальный номер фазы.
    :param user_vals: Значения пользователя в виде словаря, которые будут добавлены
                      в возвращаемый словарь после всех вычислений(Дубли будут перезаписаны
                      user_vals).
    :return: Словарь с соответствием фазы к varbinds.
    """
    stages = {0: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(0))}

    stages |= {
        num_stage: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(num_stage + 1))
        for num_stage in range(1, max_stage + 1)
    }

    usr_data = {}

    try:
        for k_k, v_v in user_vals.items():
            usr_data[k_k] = wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(v_v))
    except AttributeError:
        usr_data.clear()

    return stages | usr_data

ug405_set_stage_values = convert_val_to_num_stage_set_req_ug405(128)
swarco_stcip_set_stage_varbinds = create_stcip_set_stage_varbinds(swarco_itc2.MAX_STAGE, user_vals={8: 1})
potok_stcip_set_stage_varbinds = create_stcip_set_stage_varbinds(potok.MAX_STAGE)


class ScnConverterMixin:

    @classmethod
    def get_scn_as_ascii_from_scn_as_chars(cls, scn_as_chars_string: str) -> str | None:
        return cls.convert_chars_string_to_ascii_string(scn_as_chars_string)

    @classmethod
    def convert_ascii_string_to_chars(cls, scn_as_ascii: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        .1.6.67.79.50.48.56.48
        """
        splitted = scn_as_ascii.split('.')
        num_chars = int(splitted[2])
        scn_as_chars = ''.join([chr(int(c)) for c in splitted[3:]])
        logger.debug(f'scn_as_chars: {scn_as_chars}')
        assert num_chars == len(scn_as_chars)
        return scn_as_chars

    @classmethod
    def convert_chars_string_to_ascii_string(cls, scn: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """
        return convert_chars_string_to_ascii_string(scn)

    @classmethod
    def add_CO_to_scn(cls, scn: str) -> str | None:
        if not isinstance(scn, str) or not scn.isdigit():
            return None
        return f'CO{scn}'

    def get_scn_as_ascii_from_scn_as_chars_attr(self, scn_as_chars) -> str | None:
        if scn_as_chars is not None:
            return self.convert_chars_string_to_ascii_string(scn_as_chars)
        return None

    def get_scn_as_chars_from_scn_as_ascii(self, scn_as_ascii_string) -> str:
        if scn_as_ascii_string is not None:
            return self.convert_ascii_string_to_chars(scn_as_ascii_string)


class HexValueToIntegerStageConverter:

    @classmethod
    def get(cls, val_as_hex) -> int:
        return convert_val_as_hex_to_decimal(val_as_hex)


class AbstractStageConverterMixin:

    matches_oid_val_to_num_stage: dict[str, int] | Type[HexValueToIntegerStageConverter]

    @classmethod
    def get_num_stage_from_oid_val(cls, oid_val: str) -> int:
        """
        Сопоставляет значение оида фазы и возвращает номер фазы в десятичном представлении.
        :param oid_val: Значение оида фазы в строковом предаставлении.
        :return: Номер фазы в десятичном представлении.
        """
        return cls.matches_oid_val_to_num_stage.get(oid_val)


class StageConverterMixinSwarco(AbstractStageConverterMixin):

    matches_oid_val_to_num_stage = {
        '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0
    }


class StageConverterMixinPotokS(AbstractStageConverterMixin):

    matches_oid_val_to_num_stage = {
        str(k) if k < 66 else str(0): v if v < 65 else 0 for k, v in zip(range(2, 67), range(1, 66))
    }


class StageConverterMixinUg405(AbstractStageConverterMixin):

    matches_oid_val_to_num_stage = HexValueToIntegerStageConverter


class AbstractVarbinds:
    states_oids: T_Oids
    states_varbinds: T_Varbinds
    set_stage_varbinds: dict[int, T_Varbinds]

    def get_varbinds_current_states(self):
        return self.states_varbinds

    def get_varbinds_set_stage(self, num_stage: int):
        return [self.set_stage_varbinds[num_stage]]


class VarbSwarco(AbstractVarbinds):
    states_oids = oids.oids_state_swarco
    states_varbinds = create_varbinds(oids.oids_state_swarco)
    set_stage_varbinds = swarco_stcip_set_stage_varbinds


class VarbPotokS(AbstractVarbinds):
    states_oids = oids.oids_state_potok_s
    states_varbinds = tuple(wrap_oid_by_object_type(oid) for oid in oids.oids_state_potok_s)
    set_stage_varbinds = swarco_stcip_set_stage_varbinds


class CommonVarbindsUg405:

    max_scn = 9999
    num_CO_prefix = 'CO'

    operation_mode_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode)
    operation_mode1_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode, Integer32(1))
    operation_mode2_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode, Integer32(2))
    operation_mode3_varbind = wrap_oid_by_object_type(Oids.utcType2OperationMode, Integer32(3))

    site_id_varbind = wrap_oid_by_object_type(Oids.utcReplySiteID)

    hex_vals128 = {i: OctetString(hexValue=ug405_set_stage_values.get(str(i))) for i in range(1, 129)}

    integer_vals128 = {i: Integer32(i) for i in range(129)}
    integer32_val1 = Integer32(1)
    integer32_val2 = Integer32(2)
    integer32_val3 = Integer32(3)

    states_varbinds: dict[str, Iterable[T_Varbinds]]
    states_oids: T_Oids

    @classmethod
    def get_operation_mode_varbinds(cls, op_mode_val: int) -> ObjectType:
        if op_mode_val == 3:
            return cls.operation_mode3_varbind
        if op_mode_val == 2:
            return cls.operation_mode2_varbind
        return cls.operation_mode1_varbind

    def get_varbinds_current_states(self, scn_as_ascii: str):
        try:
            return self.states_varbinds[scn_as_ascii]
        except KeyError:
            return add_scn_to_oids(
                scn_as_ascii, self.states_oids, True
            )

    def get_varbinds_set_stage(
            self,
            scn_as_ascii: str,
            num_stage: int
    ) -> T_Varbinds:
        if 0 < num_stage < 129:
            return (
                self.operation_mode3_varbind,
                wrap_oid_by_object_type(f'{str(Oids.utcControlTO)}{scn_as_ascii}', self.integer32_val1),
                wrap_oid_by_object_type(f'{Oids.utcControlFn}{scn_as_ascii}', self.hex_vals128.get(num_stage)),
            )
        return (self.operation_mode1_varbind,)


class VarbPotokP(CommonVarbindsUg405):
    states_oids = oids.oids_state_potok_p
    states_varbinds = create_varbinds_get_state_with_scn(oids.oids_state_potok_p)


class VarbPeek(CommonVarbindsUg405):
    """ Класс для создания синглтона varbinds peek """


# Синглтоны varbinds для каждого типа дк
swarco_stcip_varbinds = VarbSwarco()
potok_stcip_varbinds = VarbPotokS()
potok_ug405_varbinds = VarbPotokP()
peek_ug405_varbinds = VarbPeek()


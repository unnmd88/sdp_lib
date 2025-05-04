import abc
import asyncio
import dataclasses
import math
import sys
import time
from  typing import Type
from collections.abc import (
    Sequence,
    Iterable,
    Callable
)
from dataclasses import asdict
from typing import TypeAlias, TypeVar

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

from sdp_lib.management_controllers.snmp import oids
from sdp_lib.management_controllers.snmp.user_types import (
    T_Oids,
    T_Varbinds, T_Varbind
)
from sdp_lib.management_controllers.snmp.oids import (
    Oids,
    oids_scn_required
)


Oid_Value: TypeAlias = TypeVar('Oid_Value',
    Unsigned32, Integer, OctetString, rfc1905.unSpecified
)


def convert_val_to_num_stage_set_req_ug405(
        max_stage: int
) -> dict:
    stg_mask = ['01', '02', '04', '08', '10', '20', '40', '80']
    return {str(k): v for k, v in enumerate((f'{i}{j * "00"}' for j in range(max_stage // 8) for i in stg_mask), 1)}


def wrap_oid_by_object_type(
        oid: Oids | str,
        val: Oid_Value = rfc1905.unSpecified
) -> ObjectType:
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
    start_time = time.perf_counter()
    varbinds_get_state = {}
    for num_co in range(num_co_min, num_co_max + 1):
        scn = convert_chars_string_to_ascii_string(f'{prefix}{str(num_co)}')
        varbinds_get_state[scn] = add_scn_to_oids(scn, get_state_oids_pattern, True)
    print(f'FinS: {time.time() - start_time}')
    print(f'len(varbinds_get_state): {len(varbinds_get_state)}')
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
        print(f'Значение val: {val}')

ug405_set_stage_values = convert_val_to_num_stage_set_req_ug405(128)

swarco_stcip_set_stage_varbinds = {
                                      num_stage: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand,
                                                                         Unsigned32(num_stage + 1))
                                      for num_stage in range(1, 8)
                                  } | {8: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(1)),
                                       0: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(0))}

potok_stcip_set_stage_varbinds = {
                                     num_stage: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand,
                                                                        Unsigned32(num_stage + 1))
                                     for num_stage in range(1, 129)
                                 } | {0: wrap_oid_by_object_type(Oids.swarcoUTCTrafftechPhaseCommand, Unsigned32(0))}



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


class AbstractVarbindsWithScn:
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


class VarbPotokP(AbstractVarbindsWithScn):
    states_oids = oids.oids_state_potok_p
    states_varbinds = create_varbinds_get_state_with_scn(oids.oids_state_potok_p)


class VarbPeek(AbstractVarbindsWithScn):
    """ Класс для создания синглтона varbinds peek """


# Синглтоны varbinds для каждого типа дк
swarco_stcip_varbinds = VarbSwarco()
potok_stcip_varbinds = VarbPotokS()
potok_ug405_varbinds = VarbPotokP()
peek_ug405_varbinds = VarbPeek()

VarbindsUg405 = ''


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
        # print(f'scn_as_chars: {scn_as_chars}')
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


if __name__ == '__main__':
    o = add_scn_to_oids('aaaaaaa', oids.oids_state_potok_p)
    print(o)
    print('-' * 50)
    o = add_scn_to_oids('aaaaaaa', oids.oids_state_potok_p, wrap_oids_by_object_type=True)
    print(o)

    # build_test_obj()

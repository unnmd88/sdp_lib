import functools
import math
import time
from typing import Callable, Any

from pysnmp.proto import rfc1905
from pysnmp.proto.rfc1902 import Unsigned32, Integer32, Integer, OctetString
from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

from sdp_lib.management_controllers.snmp import oids
# from sdp_lib.management_controllers.snmp.snmp_config import swarco_stcip, AllowedControllers
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.management_controllers.snmp.set_commands import AvailableGetCommands, AvailableSetCommands




def async_timed():
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapped(*args, **kwargs) -> Any:
            print(f"starting {func} with args {args} {kwargs}")
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                end = time.time()
                total = end - start
                print(f"finished {func} in {total:4f} second(s)")

        return wrapped

    return wrapper


T_Varbinds = tuple[ObjectType, ...]


def process_varbinds_as_dict(varbinds: T_Varbinds) -> dict[str, str]:
    return {str(oid): val.prettyPrint() for oid, val in varbinds}


def remove_scn_from_oid(oid: str, scn_as_ascii_string) -> str:
    return oid.replace(scn_as_ascii_string, '')




class AbstractConverters:

    state_oids: tuple[ObjectType, ...]

    def get_varbinds_for_get_state(self) -> list[ObjectType]:
        raise NotImplementedError()


class AbstractStcipConverters:

    matches_val_from_num_stage_to_oid_vals: dict

    @classmethod
    def get_num_stage_from_oid_val(cls, val: str) -> int | None:
        return cls.matches_val_from_num_stage_to_oid_vals.get(val)


class AbstractUg405PConverters:

    oids_scn_required = oids.oids_scn_required
    state_oids: tuple[Oids | str, ...]
    scn_varbind: ObjectType
    get_operation_mode_varbind = ObjectType(ObjectIdentity(Oids.utcType2OperationMode))
    set_operation_mode2_varbind = ObjectType(ObjectIdentity(Oids.utcType2OperationMode, Integer32(2)))
    set_operation_mode3_varbind = ObjectType(ObjectIdentity(Oids.utcType2OperationMode, Integer32(3)))

    @classmethod
    def convert_hex_to_decimal(cls, val: str) -> int | None:
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

    @classmethod
    def get_num_stage_from_oid_val(cls, val: str) -> int | None:
        return cls.convert_hex_to_decimal(val)

    @staticmethod
    def convert_chars_string_to_ascii_string(scn: str) -> str:
        """
        Генерирует SCN
        :param scn -> символы строки, которые необходимо конвертировать в scn
        :return -> возвращет scn
        """
        return f'.1.{str(len(scn))}.{".".join([str(ord(c)) for c in scn])}'

    @classmethod
    def get_scn_as_ascii_from_scn_as_chars(cls, scn_as_chars_string: str) -> str | None:
        return cls.convert_chars_string_to_ascii_string(scn_as_chars_string)

    # @classmethod
    # def add_scn_to_oids(
    #         cls,
    #         oids: tuple[Oids, ...] | list[Oids],
    #         scn_as_chars_string: str = None,
    #         scn_as_ascii_string: str = None,
    #         wrap_oid_by_object_identity: bool = False
    # ) -> list[Oids | str | ObjectType]:
    #     if scn_as_ascii_string:
    #         scn = scn_as_ascii_string
    #     elif scn_as_chars_string:
    #         scn = cls.get_scn_as_ascii_from_scn_as_chars(
    #             scn_as_chars_string
    #         )
    #     else:
    #         raise ValueError(
    #             'Необходимо передать в функию один из аргументов:\n'
    #             'scn_as_chars_string(Например: CO1111) или scn_as_ascii_string(Например: .1.3.22.22.22)'
    #         )
    #     if wrap_oid_by_object_identity:
    #         return [
    #             ObjectType(ObjectIdentity(f'{oid}{scn}')) if oid in cls.oids_scn_required
    #             else ObjectType(ObjectIdentity(oid))
    #             for oid in oids
    #         ]
    #     return [
    #         f'{oid}{scn}' if oid in cls.oids_scn_required else oid
    #         for oid in oids
    #     ]

    @classmethod
    def add_scn_to_oids(
            cls,
            oids_without_val: tuple[Oids, ...] | list[Oids],
            scn_as_ascii_string: str = None,
            wrap_oid_by_object_identity: bool = False
    ) -> list[Oids | str | ObjectType]:


        # if wrap_oid_by_object_identity:
        #     return [
        #         ObjectType(ObjectIdentity(f'{oid}{scn_as_ascii_string}')) if oid in cls.oids_scn_required
        #         else ObjectType(ObjectIdentity(oid))
        #         for oid in oids_without_val
        #     ]
        for oid in oids_without_val:
            yield f'{oid}{scn_as_ascii_string}' if oid in cls.oids_scn_required else oid

        # return [
        #     f'{oid}{scn_as_ascii_string}' if oid in cls.oids_scn_required else oid
        #     for oid in oids_without_val
        # ]

    @classmethod
    def wrap_by_object_type_oids_with_val(
            cls,
            scn_as_ascii_string,
            oids_with_val: list[tuple[Oids | str, Any]]
    ):

        return [
                ObjectType(ObjectIdentity(f'{oid}{scn_as_ascii_string}')) if oid in cls.oids_scn_required
                else ObjectType(ObjectIdentity(oid))
                for oid in oids_with_val
            ]



    @classmethod
    def get_varbinds_for_get_state(
            cls,
            *,
            scn_as_ascii_string: str = None,
            scn_as_chars_string: str = None
    ) -> list[ObjectType]:
        print(f'scn_as_ascii_string: {scn_as_ascii_string}')
        print(f'scn_as_chars_string: {scn_as_chars_string}')
        return cls.add_scn_to_oids(
            oids_without_val=cls.state_oids,
            scn_as_ascii_string=scn_as_ascii_string,
            scn_as_chars_string=scn_as_chars_string,
            wrap_oid_by_object_identity=True
        )

    @classmethod
    def get_varbinds(cls):
        pass


class SwarcoConverters(AbstractStcipConverters):

    state_oids = oids.oids_state_swarco
    matches_val_from_num_stage_to_oid_vals = {
        '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '1': 8, '0': 0
    }
    payload_for_set_stage = {
        num_stage: Unsigned32(num_stage + 1) for num_stage in range(1, 8)
    } | {8: Unsigned32(1), 0: Unsigned32(0)}
    varbinds_get_state = [
        ObjectType(ObjectIdentity(oid)) for oid in oids.oids_state_swarco
    ]

    @classmethod
    def get_varbinds_for_set_stage(cls, num_stage: int):
        # *[ObjectType(ObjectIdentity(oid), val) for oid, val in oids]
        return [
            ObjectType(ObjectIdentity(Oids.swarcoUTCTrafftechPhaseCommand), cls.payload_for_set_stage.get(num_stage))
        ]

    @classmethod
    def get_varbinds_for_get_state(cls) -> list[ObjectType]:
        return cls.varbinds_get_state


class PotokSConverters(AbstractStcipConverters):

    matches_val_from_num_stage_to_oid_vals = {
        str(k) if k < 66 else str(0): v if v < 65 else 0 for k, v in zip(range(2, 67), range(1, 66))
    }


class PotokPConverters(AbstractUg405PConverters):

    state_oids = oids.oids_state_potok_p
    scn_varbind = ObjectType(ObjectIdentity(oids.Oids.utcReplySiteID))

    varbinds_for_get_request = {
        AvailableGetCommands: oids.oids_state_potok_p,
    }

    def get_varbinds_get_request(
            cls,
            scn_as_ascii: str,
            request_entity,
    ):
        return cls.add_scn_to_oids(
            oids_without_val=cls.varbinds_for_get_request.get(request_entity),
            scn_as_ascii_string=scn_as_ascii,
            wrap_oid_by_object_identity=True
        )

    def get_varbinds_set_request(
            cls,
            scn_as_ascii: str,
            request_entity: list[tuple[AvailableSetCommands, Any]],
    ):
        pass


class PeekConverters(AbstractUg405PConverters):

    scn_varbind = ObjectType(ObjectIdentity(oids.Oids.utcType2Reply))

    matches = {
        AvailableGetCommands: ...,

    }

    # def get_varbinds(
    #         cls,
    #         request_entity = None,
    #         oids = None
    # ):


def convert_chars_string_to_ascii_string(scn_as_chars: str) -> str:
    """
    Генерирует SCN
    :param scn -> символы строки, которые необходимо конвертировать в scn
    :return -> возвращет scn
    """
    return f'.1.{str(len(scn_as_chars))}.{".".join([str(ord(c)) for c in scn_as_chars])}'


def convert_val_to_num_stage_set_req_ug405(max_stage: int) -> dict:

    stg_mask = ['01', '02', '04', '08', '10', '20', '40', '80']
    return {str(k): v for k, v in enumerate((f'{i}{j * "00"}' for j in range(max_stage//8) for i in stg_mask), 1)}


def wrap_oid_by_object_type(oid, val: Unsigned32 | Integer | OctetString = None):
    return ObjectType(ObjectIdentity(oid), val if val is not None else rfc1905.unSpecified)


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
        print(f'scn_as_chars: {scn_as_chars}')
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


# print(x)
# print(dataclasses.asdict(x))
# print(dataclasses.fields(A))




if __name__ == '__main__':
    print(swarco_stcip._asdict())





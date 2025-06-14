from collections.abc import (
    Iterable,
    MutableMapping, Collection
)
from typing import (
    TypeVar,
    Literal,
    TypeAlias, Type
)

from pysnmp.proto import rfc1905
from pysnmp.proto.api.v2c import (
    Unsigned32,
    Integer,
    OctetString
)
from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.parsers.snmp_parsers.varbinds_parsers import ParsersVarbindsSwarco, \
    ParsersVarbindsPotokS, ParsersVarbindsPotokP, ParsersVarbindsPeek
from sdp_lib.management_controllers.snmp.oids import Oids
from sdp_lib.modbus.data_helpers import Description


alias_matched_bit_states_to_descr: TypeAlias = (
    Iterable[Iterable[tuple[bool, ...], Description]] | MutableMapping[tuple[bool, ...], Description]
)
alias_matched_bit_addr_to_descr: TypeAlias = (
    Iterable[int, Description] | MutableMapping[int, Description]
)

T_Oids: TypeAlias = Collection[Oids | str]
T_Oid: TypeAlias = Oids | str
T_Varbinds: TypeAlias = Collection[ObjectType]
T_Varbind: TypeAlias = ObjectType
T_Parsers = TypeVar('T_Parsers')
A_Parsers: TypeAlias = Type[ParsersVarbindsSwarco | ParsersVarbindsPotokS | ParsersVarbindsPotokP | ParsersVarbindsPeek]
Oid_Value = TypeVar('Oid_Value', Unsigned32, Integer, OctetString, rfc1905.unSpecified)

StcipController: TypeAlias = Literal[AllowedControllers.SWARCO, AllowedControllers.POTOK_S]

RequestModes: TypeAlias = Literal['get', 'set', 'get_next']
ParserMethodType: TypeAlias = Literal['pretty', 'default']

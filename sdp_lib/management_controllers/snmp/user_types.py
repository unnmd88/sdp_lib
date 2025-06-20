import collections.abc
from typing import (
    TypeVar,
    Literal,
    TypeAlias
)
from collections import abc
from pysnmp.proto import rfc1905
from pysnmp.proto.api.v2c import (
    Unsigned32,
    Integer,
    OctetString
)
from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.snmp.oids import Oids


# T_Oids: TypeAlias = tuple[Oids | str, ...] | list[Oids | str]
T_Oids: TypeAlias = abc.Sequence[Oids | str]
T_Oid: TypeAlias = Oids | str
# T_Varbinds: TypeAlias = tuple[ObjectType, ...] | list[ObjectType]
T_Varbinds: TypeAlias = abc.Sequence[ObjectType]
T_Varbind: TypeAlias = ObjectType
T_Parsers = TypeVar('T_Parsers')
Oid_Value = TypeVar('Oid_Value', Unsigned32, Integer, OctetString, rfc1905.unSpecified)

StcipController: TypeAlias = Literal[AllowedControllers.SWARCO, AllowedControllers.POTOK_S]

RequestModes: TypeAlias = Literal['get', 'set', 'get_next']
ParserMethodType: TypeAlias = Literal['pretty', 'default']

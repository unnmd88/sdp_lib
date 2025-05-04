from typing import (
    TypeVar,
    Literal,
    TypeAlias
)

from pysnmp.proto import rfc1905
from pysnmp.proto.api.v2c import (
    Unsigned32,
    Integer,
    OctetString
)
from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.snmp.oids import Oids


T_Oids: TypeAlias = TypeVar('T_Oids', tuple[Oids | str, ...], list[Oids | str])
T_Varbinds: TypeAlias = TypeVar('T_Varbinds', tuple[ObjectType, ...], list[ObjectType])
T_Varbind: TypeAlias = TypeVar('T_Varbind', bound=ObjectType)
T_Parsers: TypeAlias = TypeVar('T_Parsers')
Oid_Value: TypeAlias = TypeVar('Oid_Value', Unsigned32, Integer, OctetString, rfc1905.unSpecified)

StcipContrloller: TypeAlias = Literal[AllowedControllers.SWARCO, AllowedControllers.POTOK_S]

RequestModes: TypeAlias = Literal['get', 'set', 'get_next']
ParserMethodType: TypeAlias = Literal['pretty', 'default']

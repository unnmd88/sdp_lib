from typing import TypeVar, Literal, TypeAlias

from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.snmp.oids import Oids


T_Oids = TypeVar('T_Oids', tuple[Oids | str, ...], list[Oids | str])
T_Varbinds = TypeVar('T_Varbinds', tuple[ObjectType, ...], list[ObjectType])
T_Parsers = TypeVar('T_Parsers')

RequestModes: TypeAlias = Literal['get', 'set', 'get_next']
ParserMethodType: TypeAlias = Literal['pretty', 'default']

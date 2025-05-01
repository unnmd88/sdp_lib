from enum import IntEnum, StrEnum


class AvailableSetCommands(IntEnum):

    stage = 1
    flash = 2
    dark  = 3

class AvailableGetCommands(IntEnum):

    current_state = 1


class SnmpEntity(StrEnum):
    snmp_get = 'get'
    snmp_set = 'set'
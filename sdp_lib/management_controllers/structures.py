from enum import IntEnum


class HostResponseStructure(IntEnum):

    ERRORS        = 0
    DATA_RESPONSE = 1
    RAW_RESPONSE  = 2


class SnmpResponseStructure(IntEnum):

    ERROR_INDICATION = 0
    ERROR_STATUS     = 1
    ERROR_INDEX      = 2
    VAR_BINDS        = 3

class HttpResponseStructure(IntEnum):

    ERROR    = 0
    CONTENT  = 1


class InputsStructure(IntEnum):

    INDEX     = 0
    NUM       = 1
    NAME      = 2
    STATE     = 3
    TIME      = 4
    ACTUATOR  = 5
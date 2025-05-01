import os
from enum import StrEnum

cookies = {os.getenv('peek_web_k'): os.getenv('peek_web_v')}


class ActuatorAsChar(StrEnum):
    VF     = '-'
    OFF    = 'ВЫКЛ'
    ON     = 'ВКЛ'


class ActuatorAsValue(StrEnum):
    VF     = '0'
    OFF    = '1'
    ON     = '2'


matches_actuators = {
    ActuatorAsChar.VF: ActuatorAsValue.VF,
    ActuatorAsChar.OFF: ActuatorAsValue.OFF,
    ActuatorAsChar.ON: ActuatorAsValue.ON,
    ActuatorAsValue.VF: ActuatorAsChar.VF,
    ActuatorAsValue.OFF: ActuatorAsChar.OFF,
    ActuatorAsValue.ON: ActuatorAsChar.ON
}
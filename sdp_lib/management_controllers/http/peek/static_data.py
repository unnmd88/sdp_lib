import os
from enum import StrEnum
from functools import cached_property

cookies = {os.getenv('peek_web_k'): os.getenv('peek_web_v')}

VF_as_chars = '-'
OFF_as_chars = 'ВЫКЛ'
ON_as_chars = 'ВКЛ'

VF_as_value = '0'
OFF_as_value = '1'
ON_as_value = '2'

matches_actuators = {
    VF_as_chars: VF_as_value,
    OFF_as_chars: OFF_as_value,
    ON_as_chars: ON_as_value,
    VF_as_value: VF_as_chars,
    OFF_as_value: OFF_as_chars,
    ON_as_value: ON_as_chars
}


class Actuator(StrEnum):
    VF_as_chars = VF_as_chars
    OFF_as_chars = OFF_as_chars
    ON_as_chars = ON_as_chars

    VF_as_value = VF_as_value
    OFF_as_value = OFF_as_value
    ON_as_value = ON_as_value

    @classmethod
    def get_reverse_value(cls, chars_or_value):
        return matches_actuators[chars_or_value]

    @classmethod
    def pretty_print(cls, name: str, chars_or_value):
        if chars_or_value in (cls.VF_as_chars, cls.VF_as_value):
            val = 'ВФ'
        elif chars_or_value in (cls.ON_as_chars, cls.OFF_as_chars):
            val = chars_or_value
        else:
            val = matches_actuators[chars_or_value]
        return f'{name}={val}'


class ActuatorAsChar(StrEnum):
    VF     = '-'
    OFF    = 'ВЫКЛ'
    ON     = 'ВКЛ'


class ActuatorAsValue(StrEnum):
    VF     = '0'
    OFF    = '1'
    ON     = '2'





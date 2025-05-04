import enum
import typing


class MaxStage(enum.IntEnum):

    swarco_itc2  = 8
    potok_p      = 128
    potok_s      = 128
    peek         = 32


class BaseConfig(typing.NamedTuple):
    MAX_STAGE: int


potok = BaseConfig(128)
potok_p = BaseConfig(128)
potok_s = BaseConfig(128)
swarco_itc2 = BaseConfig(8)
peek = BaseConfig(32)


if __name__ == '__main__':
    print(swarco_itc2)

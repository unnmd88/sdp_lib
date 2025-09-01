import itertools
from dataclasses import dataclass, asdict, fields, astuple
from enum import IntEnum
from typing import NamedTuple


class N(NamedTuple):
    a: int
    b: list


if __name__ == '__main__':
    inst = N(1, [])
    inst2 = N(1, [312])

    print(inst)
    print(inst2)

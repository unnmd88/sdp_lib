import itertools
from dataclasses import dataclass, asdict, fields, astuple
from enum import IntEnum


class E(IntEnum):
    x = 1
    y = 2


if __name__ == '__main__':
    try:
        check_list = bool(E(5))
    except ValueError:
        print(check_list)
        check_list = False
    print(check_list)

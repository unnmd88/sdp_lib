import itertools
from dataclasses import dataclass, asdict, fields, astuple

from pyasn1.type.univ import Sequence


class T2:
    __slots__ = ('a', 'b', 'c')

    def __init__(self, a, b, c):
        self.a = a
        self.b = b

inst = T2(1, 2, 321)
print(inst.a)
inst.a = 5
print(inst.a)
if __name__ == '__main__':
    pass
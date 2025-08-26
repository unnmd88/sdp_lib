import itertools
from dataclasses import dataclass, asdict, fields

from pyasn1.type.univ import Sequence


@dataclass
class T:
    one: str
    two: int
    three: Sequence

    def __iter__(self):
        return (pair for pair in asdict(self).items())
ob = T('1', 2, [1, 2 , 2])

chain = itertools.chain(
            (1, 1),
            (pair for pair in asdict(ob).items()),
            (2, 2)

        )

for el in chain:
    print(el)


if __name__ == '__main__':
    pass
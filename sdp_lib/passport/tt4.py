import itertools
from dataclasses import dataclass, asdict, fields, astuple



v14 = [i for i in range(15)]
v15 = [str(i) for i in range(16)]


if __name__ == '__main__':

    for el in itertools.chain([1, 2, 3, 5], [None], ['6', '7']):
        print(el)

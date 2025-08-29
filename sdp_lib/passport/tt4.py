import itertools
from dataclasses import dataclass, asdict, fields, astuple



v14 = [i for i in range(15)]
v15 = [str(i) for i in range(16)]

def _get_values(data):
    if len(data) == 14:
        for i, cell in enumerate(data):
            if i == 10:
                yield None
            else:
                yield cell
    else:
        for cell in data:
            yield cell

if __name__ == '__main__':

    # for el in _get_values([1, 2, 3]):
    #     print(el)
    print(list(_get_values(v14)))
    print(list(_get_values(v15)))
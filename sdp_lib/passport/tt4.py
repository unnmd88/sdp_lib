import itertools
import re
from dataclasses import dataclass, asdict, fields, astuple
from enum import IntEnum
from typing import NamedTuple


reg = re.match('^\d{,2}\.\d$', '01.2')



if __name__ == '__main__':
    val_s = str('11')
    val_f = float(val_s)

    print('-1'.isdigit())
    print(int('-1'))



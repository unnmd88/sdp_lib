import dataclasses
import operator
import re
import time
from collections import Counter
from collections.abc import MutableSequence
from dataclasses import dataclass, field, astuple
from enum import StrEnum
from itertools import filterfalse, count, combinations_with_replacement
from typing import NamedTuple, AnyStr, Any

from sdp_lib.passport.constants import DirectionEntities, RowNames
import logging
import asyncio
# from deep_translator import GoogleTranslator
from docx import Document



data = '1\tТранспортное\t1,8,9\n2\tТранспортное\t1,2\n3\tТранспортное\t4\n4\tПоворотное\t2,3,4\n5\tТранспортное\t3,6,7,8,9,10\n6\tТранспортное\t5,6,7,10\n7\tТранспортное\t4,5,8,9\n8\tТранспортное\t1,2,3,4\n9\tПешеходное\t2,3\n10\tТранспортное\t1,5,6,7,8,9,10\n11\tПешеходное\t1,2,3,4,5,6,8,9\n12\tТранспортное\t2,3,4,5,6,7,10\n13\tТранспортное\t6,7,10\n14\tТранспортное\t1\n15\tПоворотное\t5,6,7,10\n16\tТранспортное\t5,6,7,8,9,10\n17\tТранспортное\t2,3,4\n18\tТранспортное\t7,10\n19\tТранспортное\t3,4,5,8,9,10\n20\tПешеходное\t3\n21\tТранспортное\t1,2,3,4\n22\tПешеходное\t1,2,3,4,5,8,9\n23\tТранспортное\t6,7\n24\tТранспортное\tПост.краси.\n'


def read_file(filepath) -> str:
    with open(filepath, encoding='utf-8') as f:
        return ''.join(line for line in f)


def write_to_file(filepath, to_write):
    with open(filepath, 'w') as f:
        f.writelines(to_write)


if __name__ == '__main__':
    print(re.match('', ''))










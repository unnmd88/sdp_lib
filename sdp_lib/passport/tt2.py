import dataclasses
import operator
import re
import time
from collections import Counter
from collections.abc import MutableSequence
from dataclasses import dataclass, field, astuple
from itertools import filterfalse, count
from typing import NamedTuple, AnyStr, Any

from sdp_lib.passport.constants import DirectionTypes, RowNames
import logging
import asyncio
# from deep_translator import GoogleTranslator
import pymorphy3


data = '1\tТранспортное\t1,8,9\n2\tТранспортное\t1,2\n3\tТранспортное\t4\n4\tПоворотное\t2,3,4\n5\tТранспортное\t3,6,7,8,9,10\n6\tТранспортное\t5,6,7,10\n7\tТранспортное\t4,5,8,9\n8\tТранспортное\t1,2,3,4\n9\tПешеходное\t2,3\n10\tТранспортное\t1,5,6,7,8,9,10\n11\tПешеходное\t1,2,3,4,5,6,8,9\n12\tТранспортное\t2,3,4,5,6,7,10\n13\tТранспортное\t6,7,10\n14\tТранспортное\t1\n15\tПоворотное\t5,6,7,10\n16\tТранспортное\t5,6,7,8,9,10\n17\tТранспортное\t2,3,4\n18\tТранспортное\t7,10\n19\tТранспортное\t3,4,5,8,9,10\n20\tПешеходное\t3\n21\tТранспортное\t1,2,3,4\n22\tПешеходное\t1,2,3,4,5,8,9\n23\tТранспортное\t6,7\n24\tТранспортное\tПост.краси.\n'

a = [1, 4,]


def read_file(filepath) -> str:
    with open(filepath, encoding='utf-8') as f:
        return ''.join(line for line in f)


def write_to_file(filepath, to_write):
    with open(filepath, 'w') as f:
        f.writelines(to_write)

def gen(x):
    if x > 1:
        yield x

txt = 'Ошибка типа направления'


if __name__ == '__main__':
    # read_file(f'directions')
    # raw_data_directions = '1\tТранспортное\t1,8,9\n2\tТранспортное\t1,2\n3\tТранспортное\t4\n4\tПоворотное\t2,3,4\n5\tТранспортное\t3,6,7,8,9,10\n6\tТранспортное\t5,6,7,10\n7\tТранспортное\t4,5,8,9\n8\tТранспортное\t1,2,3,4\n9\tПешеходное\t2,3\n10\tТранспортное\t1,5,6,7,8,9,10\n11\tПешеходное\t1,2,3,4,5,6,8,9\n12\tТранспортное\t2,3,4,5,6,7,10\n13\tТранспортное\t6,7,10\n14\tТранспортное\t1\n15\tПоворотное\t5,6,7,10\n16\tТранспортное\t5,6,7,8,9,10\n17\tТранспортное\t2,3,4\n18\tТранспортное\t7,10\n19\tТранспортное\t3,4,5,8,9,10\n20\tПешеходное\t3\n21\tТранспортное\t1,2,3,4\n22\tПешеходное\t1,2,3,4,5,8,9\n23\tТранспортное\t6,7\n24\tТранспортное\tПост.краси.\n'.rstrip()
    # raw_data_stages = (
    #     '1\t1\t1, 2, 8, 10, 11, 14, 21, 22\n'
    #     '2\t2\t2, 4, 8, 9, 11, 12, 17, 22, 25\n'
    #     '3\t3\t4, 5, 8, 9, 11, 12, 17, 19, 20, 21, 22\n'
    #     '4\t4\t3, 4, 7, 8, 11, 12, 17, 19, 21, 22\n'
    #     '5\t5\t6, 7, 10, 11, 12, 15, 16, 19, 22\n'
    #     '6\t6\t5, 6, 10, 11, 12, 13, 15, 16, 23, 25\n'
    #     '7\t7\t5, 6, 10, 12, 13, 15, 16, 18, 23, 25\n'
    #     '8\t8\t1, 5, 7, 10, 11, 16, 19, 22\n'
    #     '9\t9\t1, 5, 7, 10, 11, 16, 19, 22\n'
    #     '10\t10\t5, 6, 10, 12, 13, 15, 16, 18, 19\n'.rstrip()
    # )
    read_data = read_file('directions_example')
    print(repr(read_data))
    print(read_data)







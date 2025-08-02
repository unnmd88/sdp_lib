import dataclasses
import operator
import re
from collections import Counter
from collections.abc import MutableSequence
from dataclasses import dataclass, field, astuple
from typing import NamedTuple

from sdp_lib.passport.constants import DirectionTypes
import logging
import asyncio
# from deep_translator import GoogleTranslator


data = '1\tТранспортное\t1,8,9\n2\tТранспортное\t1,2\n3\tТранспортное\t4\n4\tПоворотное\t2,3,4\n5\tТранспортное\t3,6,7,8,9,10\n6\tТранспортное\t5,6,7,10\n7\tТранспортное\t4,5,8,9\n8\tТранспортное\t1,2,3,4\n9\tПешеходное\t2,3\n10\tТранспортное\t1,5,6,7,8,9,10\n11\tПешеходное\t1,2,3,4,5,6,8,9\n12\tТранспортное\t2,3,4,5,6,7,10\n13\tТранспортное\t6,7,10\n14\tТранспортное\t1\n15\tПоворотное\t5,6,7,10\n16\tТранспортное\t5,6,7,8,9,10\n17\tТранспортное\t2,3,4\n18\tТранспортное\t7,10\n19\tТранспортное\t3,4,5,8,9,10\n20\tПешеходное\t3\n21\tТранспортное\t1,2,3,4\n22\tПешеходное\t1,2,3,4,5,8,9\n23\tТранспортное\t6,7\n24\tТранспортное\tПост.краси.\n'

a = [1, 4,]

def t1(x=None, y=None, z=None,m=None,):
    print(f'x: {x} ')
    print(f'y: {y} ')
    print(f'z: {z} ')
    print(f'm: {m} ')

def read_file(filepath):
    with open(filepath) as f:
        for line in f:
            print(f'line: {line.rstrip()!r}')


txt = 'Ошибка типа направления'
if __name__ == '__main__':
    t1('xppp', *a)
    read_file(f'directions')




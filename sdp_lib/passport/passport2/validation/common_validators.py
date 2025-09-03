import itertools
import re
from collections import defaultdict
from collections.abc import Iterable, MutableMapping, MutableSequence
from itertools import zip_longest
from typing import Any

from sdp_lib.passport.constants import row0_14_dt, row1_14_dt, DirectionTablePatterns, row0_15_dt
from sdp_lib.passport.passport2.validation.base import BadValue, HeadRowData, Doubles

"""

** Проверка соответствия всех ячеек заданному образцу. **

** Проверка ячейки ** :
1. Текст
2. 

** Проверка дублей в строке(row) **

"""


# def get_bad_values(
#     target: Iterable,
#     patterns: Iterable[re.Pattern | str],
#     expected_vals: Iterable = None
# ):
#     expected_vals = expected_vals or (None for _ in target)
#     for i, (string, pattern, expected) in enumerate(zip(target, patterns, expected_vals, strict=True)):
#         print(f'i: {i}, string: {string} pattern: {pattern} expected: {expected}')
#         if re.search(pattern, string) is None:
#             yield BadValue(i, string, expected)
def get_doubles(source: MutableMapping[Any, MutableSequence[int]]):
    # for k, v in source.items():
    #     if (doubles:= len(v)) > 1:
    #         res.doubles.append(Doubles(k, v, doubles))
    return [Doubles(k, v, doubles) for k, v in source.items() if (doubles:= len(v)) > 1]


def get_data_from_row(
    target: Iterable,
    patterns: Iterable[re.Pattern | str],
    expected_vals: Iterable = None
):
    expected_vals = expected_vals or (None for _ in target)
    bad_vals = []
    tmp_doubles = defaultdict(list)
    for i, (string, pattern, expected) in enumerate(zip(target, patterns, expected_vals, strict=True)):
        # print(f'i: {i}, string: {string} pattern: {pattern} expected: {expected}')
        tmp_doubles[string].append(i)
        if re.search(pattern, string) is None:
            bad_vals.append(BadValue(i, string, expected))
    res =  HeadRowData(bad_vals, get_doubles(tmp_doubles))
    print(res)
    return res



if __name__ == '__main__':
    print(row0_14_dt)
    print(row0_15_dt)
    print(row1_14_dt)
    print(len(row1_14_dt))
    r2 = ('№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Ткж', 'Пост. красное', 'Красн.', 'Зелен.', '')
    res = [bad_val for bad_val in get_data_from_row(r2, DirectionTablePatterns.get_patterns_len(14))]
    print(res)
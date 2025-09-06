import functools
import itertools
import re
import time
from collections import defaultdict
from collections.abc import Iterable, MutableMapping, MutableSequence, Sequence, Generator, Callable, Container
from itertools import zip_longest
from typing import Any, NamedTuple

from docx import Document
from docx.table import Table, _Rows
from setuptools.command.build_ext import if_dl

from sdp_lib.passport.constants import row0_14_dt, row1_14_dt, DirectionTablePatterns, row0_15_dt, allowed_min_num_rows, \
    Patterns
from sdp_lib.passport.passport2.base2 import MessageStorage, ValidationData, CellData, \
    DirectionsOrStagesSequenceValidation
from sdp_lib.passport.passport2.check_lists import TableGeometryCheckList
from sdp_lib.passport.passport2.validation.base import Cell
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import timed, remove_chars, get_stage_or_direction_number_or_none

"""

** Проверка соответствия всех ячеек заданному образцу. **

** Проверка ячейки ** :
1. Текст
2. 

** Проверка дублей в строке(row) **

"""


def validate_geometry(
    rows: _Rows,
    allowed_lengths: Container,
    min_rows: int,
) -> TableGeometryCheckList:
    num_cols = len(rows[0].cells)
    num_rows = len(rows)
    return TableGeometryCheckList(
        allowed_lengths,
        min_rows,
        ValidationData(num_cols, num_cols in allowed_lengths),
        ValidationData(num_rows, num_rows >= min_rows),
    )


def match_cells(
    strings,
    patterns,
    duplicate_pattern_result_to_context=False
):
    if duplicate_pattern_result_to_context:
        for s, p in zip(strings, patterns, strict=True):
            res = bool(re.search(p, s))
            yield CellData(s, res, res)
    else:
        for s, p in zip(strings, patterns, strict=True):
            yield CellData(s, bool(re.search(p, s)))
    # for s, p in zip(target, patterns, strict=True):
    #     yield CellData(s,  bool(re.search(p, s)))


def validate_sequence_directions_or_stages_nums_and_create_cell(
    string: str,
    sep=',',
    always_red_pattern: str | re.Pattern = Patterns.always_red.value
) -> CellData:
    string_without_spaces = remove_chars(string, ' ')
    # if len(string_without_spaces) == 0:
    #     return False
    is_valid = (
        bool(re.match(always_red_pattern, string_without_spaces)
        or any(get_stage_or_direction_number_or_none(n) is not None for n in string_without_spaces.split(sep)))
    )
    return CellData(string, is_valid)
    # tmp_basket = set()
    # for n in split_string:
    #     num = get_int_or_float(n)
    #     if num is None:
    #         res.bad_nums.append(n)
    #     else:
    #         res.nums.append(num)
    #     if num in tmp_basket:
    #         res.doubles[num or n] += 1
    #     else:
    #         tmp_basket.add(num)
    # if not validation.is_always_red and not validation.is_empty:
    #     split_string = string_without_spaces.split(sep)
    #     tmp_basket = set()
    #     for n in split_string:
    #         num = get_int_or_float(n)
    #         if num is None:
    #             res.bad_nums.append(n)
    #         else:
    #             res.nums.append(num)
    #         if num in tmp_basket:
    #             res.doubles[num or n] += 1
    #         else:
    #             tmp_basket.add(num)



if __name__ == '__main__':
    print(row0_14_dt)
    print(row0_15_dt)
    print(row1_14_dt)
    print(len(row1_14_dt))
    r2 = ('№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Ткж', 'Пост. красное', 'Красн.', 'Зелен.', '')

    path1 = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_'
    path2 = '/home/auser/Downloads/ПД Паспорт шаблон 2025 (Копия)'
    doc = Document(f'{path1}.docx')

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

from sdp_lib.passport.constants import row0_14_dt, row1_14_dt, row0_15_dt, allowed_min_num_rows, \
    Patterns
from sdp_lib.passport.passport2.base2 import MessageStorage, ValidationData, CellData, \
    DirectionsOrStagesSequenceValidation, Comparison
from sdp_lib.passport.passport2.check_lists import TableGeometryCheckList
from sdp_lib.passport.passport2.utils import remove_spaces_and_invalid_sep
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


def match_cells_one_to_one(
    strings: Sequence[str],
    patterns: Sequence[str | re.Pattern],
    to_recover: Sequence[str] = None,
    duplicate_pattern_result_to_context=False
):
    to_recover = to_recover or (None for _ in strings)
    if duplicate_pattern_result_to_context:
        for s, p, r in zip(strings, patterns, to_recover, strict=True):
            res = bool(re.match(p, s))
            yield CellData(s, res, res, recovered=r if res else None)
    else:
        for s, p, r in zip(strings, patterns, to_recover, strict=True):
            res = bool(re.match(p, s))
            yield CellData(s, bool(re.match(p, s)), recovered=r if res else None)


def get_alias(string, patterns_and_aliases: tuple[tuple[[re.Pattern | str], str], ...]) -> str | None:
    for data in patterns_and_aliases:
        if re.match(data[0], string) is not None:
            return data[1]
    return None


def match_cells_one_string_to_many_patterns(
    string: str,
    patterns_and_aliases: Sequence[tuple[str | re.Pattern, str]],
    duplicate_pattern_result_to_context=False
):
    alias = get_alias(string, patterns_and_aliases)
    is_valid = bool(alias)

    if duplicate_pattern_result_to_context:
        return CellData(string, is_valid, is_valid, recovered=alias)
    return CellData(string, bool(alias), recovered=alias)


    #     for s, patterns_and_aliases in zip(string, patterns_and_aliases, strict=True):
    #         alias = get_alias(s, patterns_and_aliases)
    #         is_valid = bool(alias)
    #         yield CellData(s, is_valid, is_valid, recovered=alias)
    # else:
    #     for s, patterns_and_aliases in zip(strings, patterns_and_aliases, strict=True):
    #         alias = get_alias(s, patterns_and_aliases)
    #         yield CellData(s, bool(alias), recovered=alias)


def validate_sequence_directions_or_stages_nums_and_create_cell(
    string: str,
    sep=',',
    always_red_pattern: str | re.Pattern = Patterns.always_red.value
) -> CellData:
    recovered_string = remove_spaces_and_invalid_sep(string)
    is_always_red = bool(re.match(always_red_pattern, recovered_string))
    is_empty = len(recovered_string) == 0
    res = DirectionsOrStagesSequenceValidation(is_always_red, is_empty, defaultdict(int), [], [], Comparison())
    if is_empty:
        res.errors.append(Text.cell_is_empty)
        return CellData(string, False, False, extra=res)

    split_string = recovered_string.split(sep)
    for i, n in enumerate(split_string):
        num = get_stage_or_direction_number_or_none(n)
        if num is not None:
            res.nums[num] += 1
        elif num is None:
            res.bad_nums.append(n)
    if res.bad_nums:
        res.nums.clear()
        return CellData(string, False, False, extra=res)
    return CellData(string, True, recovered=recovered_string, extra=res)


    # return CellData(string, is_valid)


if __name__ == '__main__':
    print(row0_14_dt)
    print(row0_15_dt)
    print(row1_14_dt)
    print(len(row1_14_dt))
    r2 = ('№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Ткж', 'Пост. красное', 'Красн.', 'Зелен.', '')

    path1 = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_'
    path2 = '/home/auser/Downloads/ПД Паспорт шаблон 2025 (Копия)'
    doc = Document(f'{path1}.docx')

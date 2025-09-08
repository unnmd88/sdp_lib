import functools
import itertools
import re
import time
from collections import defaultdict
from collections.abc import Iterable, MutableMapping, MutableSequence, Sequence, Generator, Callable, Container
from itertools import zip_longest
from typing import Any, NamedTuple

from docx import Document
from docx.table import Table, _Rows, _Cell
from setuptools.command.build_ext import if_dl

from sdp_lib.passport.constants import row0_14_dt, row1_14_dt, row0_15_dt, allowed_min_num_rows, \
    Patterns, AllowedValues, matches
from sdp_lib.passport.passport2.base2 import MessageStorage, ValidationData, CellData, \
    DirectionsOrStagesSequenceValidation, Comparison, NumberValidation, CellMapping
from sdp_lib.passport.passport2.check_lists import TableGeometryCheckList
from sdp_lib.passport.passport2.utils import remove_spaces_and_invalid_sep, remove_left_light_spaces_from_cell_text
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

def create_default_cells(
    i_table: int,
    i_row: int,
    cells: Iterable[_Cell],
):
    for i_col, c in enumerate(cells):
        src_txt = c.text
        txt_without_spaces = remove_left_light_spaces_from_cell_text(c).text
        yield CellData(
            value=src_txt,
            recovered_val=txt_without_spaces if len(src_txt) != len(txt_without_spaces) else None,
            cell_mapping=CellMapping(i_table, i_col, i_row, c),
        )


def create_cells_for_head_row(
    i_table: int,
    i_row: int,
    cells: Iterable[_Cell],
    patterns: Iterable[str | re.Pattern],
    to_recover: Iterable[str] = None,
):
    cells_lr_strip = (remove_left_light_spaces_from_cell_text(c) for c in  cells)
    for i_col, (c, p, r) in enumerate(zip(cells_lr_strip, patterns, to_recover, strict=True)):
        cm = CellMapping(i_table, i_col, i_row, c)
        txt = c.text
        res = bool(re.match(p, txt))
        was_recovered = to_recover if len(txt) != len(r) else None
        yield CellData(
            value=txt,
            text_is_valid=res,
            context_is_valid=res,
            recovered_val=was_recovered,
            cell_mapping=cm,
            messages=MessageStorage([Text.name_error] if was_recovered else [], [])
        ).write_messages_to_table_cell()


def match_one_to_one_and_load_errors_if_has_and_create_cell(
    cell: CellMapping,
    pattern: str | re.Pattern,
    to_recover: str = None,
    duplicate_pattern_result_to_context=True
):
    txt = cell.cell.text
    res = bool(re.match(pattern, txt))
    was_recovered = to_recover if len(txt) != len(to_recover) else None
    return CellData(
        value=txt,
        text_is_valid=res,
        context_is_valid=res if duplicate_pattern_result_to_context else None,
        recovered_val=was_recovered,
        cell_mapping=cell,
        messages=MessageStorage([Text.name_error] if was_recovered else [], [])
    )


def get_alias(string, patterns_and_aliases: Sequence[tuple[re.Pattern | str, str]]) -> str | None:
    if string:
        for data in patterns_and_aliases:
            if re.match(data[0], string) is not None:
                return data[1]
    return None


def match_cells_one_string_to_many_patterns_and_create_cell(
    cell_mapping: CellMapping,
    patterns_and_aliases: Sequence[tuple[str | re.Pattern, str]],
    duplicate_pattern_result_to_context=False
):
    txt = cell_mapping.cell.text
    alias = get_alias(txt, patterns_and_aliases)
    # print(f'alias: {alias}')
    # print(f'txt: {txt}')
    is_valid = bool(alias)
    was_recovered = alias if alias is not None and len(alias) != len(txt) else None
    if alias and len(alias) == len(txt) or not txt:
        err_has_differences_in_src_text_and_alias = []
    elif alias and len(alias) != len(txt):
        err_has_differences_in_src_text_and_alias = [Text.name_error]
    elif txt and alias is None:
        err_has_differences_in_src_text_and_alias = [Text.invalid_name]
    else:
        raise AssertionError('DEBUG. Ошибка логики.')
    return CellData(
        value=txt,
        text_is_valid=is_valid,
        context_is_valid=is_valid if duplicate_pattern_result_to_context else None,
        recovered_val=was_recovered,
        converted_val=alias,
        cell_mapping=cell_mapping,
        messages=MessageStorage(err_has_differences_in_src_text_and_alias, [])
    )


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
    return CellData(string, True, recovered_txt=recovered_string, extra=res)


    # return CellData(string, is_valid)


def validate_number_and_create_cell(key_for_matches, val_to_validate: str) -> CellData:
    tv = NumberValidation([])
    try:
        val_f = float(val_to_validate.replace(',', '.', 1))
    except ValueError:
        tv.errors.append(Text.is_not_a_number)
        return CellData(val_to_validate, False, False, extra=tv)
    values: AllowedValues = matches[key_for_matches]
    if values.min <= val_f <= values.max: # OK case
        return CellData(val_to_validate, True, True, recovered_txt=int(val_f) if val_f.is_integer() else val_f, extra=tv)

    if val_f < values.min:
        err = Text.val_must_be_gt(values.min)
    elif val_f > values.max:
        err = Text.val_must_be_lt(values.max)
    else:
        raise Exception(f'Debug: val_to_validate not fully validated')
    tv.errors.append(err)
    return CellData(val_to_validate, True, False, recovered_txt=int(val_f) if val_f.is_integer() else val_f, extra=tv)




if __name__ == '__main__':
    print(row0_14_dt)
    print(row0_15_dt)
    print(row1_14_dt)
    print(len(row1_14_dt))
    r2 = ('№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Ткж', 'Пост. красное', 'Красн.', 'Зелен.', '')

    path1 = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_'
    path2 = '/home/auser/Downloads/ПД Паспорт шаблон 2025 (Копия)'
    path3 = '/home/auser/py.projects/sdp_lib/sdp_lib/passport/СО_2094_ул_Островитянова_ул_Ак_Волгина_2.docx'
    doc = Document(path3)

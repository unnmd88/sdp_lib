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

from sdp_lib.passport.constants import row0_14_dt, row1_14_dt, DirectionTablePatterns, row0_15_dt, allowed_min_num_rows
from sdp_lib.passport.passport2.base2 import MessageStorage, ValidationData, CellData
from sdp_lib.passport.passport2.check_lists import TableGeometryCheckList
from sdp_lib.passport.passport2.validation.base import Cell
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import timed

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

# def validate_geometry(*args: tuple[Callable, int, Container]) -> Generator[ValidationData, Any, None]:
#     for func, val, expected in args:
#         err_msg = func(val, expected)
#         yield ValidationData(val, expected, err_msg or None)




# def create_cell_instance_is_num_direction_or_stage(val) -> int | float | None:
#     return get_int_or_float(val)


# def get_pattern_match_results(
#     *args: tuple[re.Pattern | str, Sequence[str], Sequence | None],
#     remove_lef_right_spaces=True
# ) -> Generator[tuple[Cell, ...], Any, None]:
#     for target, patterns, expected_vals in args:
#         expected_vals = expected_vals or (None for _ in target)
#         target = target if not remove_lef_right_spaces else (s.rstrip().lstrip() for s in patterns)
#         yield tuple(
#             create_cell_instance(i, s, e, bool(re.search(p, s))) for i, (p, s, e) in
#             enumerate(zip(target, patterns, expected_vals, strict=True))
#         )


def match_cells(
    target,
    patterns,
):
    for s, p in zip(target, patterns, strict=True):
        yield CellData(s,  bool(re.search(p, s)))


def match_cells_and_get_cell_data_instance(
    target,
    patterns,
    remove_lef_right_spaces=True,
):
    target = target if not remove_lef_right_spaces else (s.rstrip().lstrip() for s in patterns)
    return (CellData(s, bool(re.search(p, s))) for s, p in zip(target, patterns, strict=True))
    # for s, p in zip(target, patterns, strict=True):
    #     yield CellData(s,  bool(re.search(p, s)))
        # yield tuple(
        #     create_cell_instance(i, s, e, bool(re.search(p, s))) for i, (p, s, e) in
        #     enumerate(zip(target, patterns, expected_vals, strict=True))
        # )



if __name__ == '__main__':
    print(row0_14_dt)
    print(row0_15_dt)
    print(row1_14_dt)
    print(len(row1_14_dt))
    r2 = ('№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Ткж', 'Пост. красное', 'Красн.', 'Зелен.', '')

    path1 = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_'
    path2 = '/home/auser/Downloads/ПД Паспорт шаблон 2025 (Копия)'
    doc = Document(f'{path1}.docx')

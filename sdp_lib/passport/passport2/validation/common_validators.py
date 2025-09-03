import functools
import itertools
import re
import time
from collections import defaultdict
from collections.abc import Iterable, MutableMapping, MutableSequence, Sequence, Generator, Callable, Container
from itertools import zip_longest
from typing import Any, NamedTuple

from setuptools.command.build_ext import if_dl

from sdp_lib.passport.constants import row0_14_dt, row1_14_dt, DirectionTablePatterns, row0_15_dt, allowed_min_num_rows
from sdp_lib.passport.passport2.base2 import MessageStorage
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

def get_int_or_float(val: str) -> int | float | None:
    """
    Основная функция, содержащая логику определения валидности номера фазы или направления.
    На вход подается строка с номером, который вернёт int или float, если номер валидный,
    иначе вернёт None.
    Допустимыми считаются следующие типы номеров: целые числа или числа через точку,
    где после точки стоит единстенная цифра от 1 до 9.
    Примеры допустимых номеоров: "1", "4", "26", "1.2", "5.1", "32.4" и т.д.
    Превращает объект val в тип int | float | None.
    :param val: Объект строки из которого будет получен объект int | float | None.
    :return: Если строка val является целым числом, возвращает int(val).
             Если строка val является числом с точкой, у которого после точки стоит
             одна единственная целая цифра от 1 до 9, функция вернёт float(val).
             Иначе возвращает None.

    Примеры
    --------
    # >>> get_int_or_float("1")
    # 1
    # >>> get_int_or_float("2.1")
    # 2.1
    # >>> get_int_or_float("3.2")
    # 3.2
    # >>> get_int_or_float("4.45")
    # None
    # >>> get_int_or_float("abracadabra")
    None

    """
    if isinstance(val, (int, float)):
        return val
    if not isinstance(val, str):
        return None
    if val.isdigit():
        return int(val)
    else:
        assumption_is_float = val.split('.')
        if len(assumption_is_float) != 2:
            return None
        before_dot, after_dot = assumption_is_float
        if len(after_dot) != 1 or not after_dot.isdigit() or not before_dot.isdigit():
            return None
        return float(val)


def check_min_num_rows(num_rows: int, expected_more_than) -> str:
    if num_rows >= allowed_min_num_rows:
        return ''
    return Text.bad_num_rows(num_rows, expected_more_than)


def check_columns_length(row_length: int, expected: Container[int]) -> str:
    if not row_length in expected:
        return Text.bad_length(row_length, expected)
    return ''


def validate_geometry(*args: tuple[Callable, int, Container]) -> Generator[Cell, Any, None]:
    for func, val, expected in args:
        err_msg = func(val, expected)
        yield Cell(None, val, expected, err_msg or None)


def create_cell_instance(
    pos,
    val,
    expected,
    is_valid,
    err_msg_val_if_is_valid=None,
) -> Cell:
    return Cell(pos, val, expected, err_msg_val_if_is_valid if is_valid else Text.bad_value(expected))


def create_cell_instance_is_num_direction_or_stage(val) -> int | float | None:
    return get_int_or_float(val)


def get_pattern_match_results(
    *args: tuple[re.Pattern | str, Sequence[str], Sequence | None],
    remove_lef_right_spaces=True
) -> Generator[tuple[Cell, ...], Any, None]:
    for target, patterns, expected_vals in args:
        expected_vals = expected_vals or (None for _ in target)
        target = target if not remove_lef_right_spaces else (s.rstrip().lstrip() for s in patterns)
        yield tuple(
            create_cell_instance(i, s, e, bool(re.search(p, s))) for i, (p, s, e) in
            enumerate(zip(target, patterns, expected_vals, strict=True))
        )


if __name__ == '__main__':
    print(row0_14_dt)
    print(row0_15_dt)
    print(row1_14_dt)
    print(len(row1_14_dt))
    r2 = ('№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Ткж', 'Пост. красное', 'Красн.', 'Зелен.', '')
    print(list(get_pattern_match_results()))
    part = functools.partial(get_pattern_match_results, (DirectionTablePatterns.get_patterns_len(14), row1_14_dt, r2))
    # print(list(pattern_match(zip(DirectionTablePatterns.get_patterns_len(14), row1_14_dt, r2, strict=True))))
    first = list(get_pattern_match_results((DirectionTablePatterns.get_patterns_len(14), row1_14_dt, r2)))
    print(first)
    # start_time = time.perf_counter()
    # for _ in range(10_000):
    #     print(next(get_pattern_match_results((DirectionTablePatterns.get_patterns_len(14), row1_14_dt, r2))))
    # print(f'время составило: {time.perf_counter() - start_time}')



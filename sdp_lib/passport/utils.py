from collections.abc import (
    MutableSequence, Iterable
)
from typing import (
    TypeVar, )

from sdp_lib.passport.passport1.base import get_int_or_float
from sdp_lib.passport.storages import Message

Numbers = int | float
NumbersContainer = TypeVar('NumbersContainer', tuple, list, set, frozenset)


# def get_int_or_float(val: str) -> int | float | None:
#     """
#     Превращает объект val в тип int | float | None.
#     :param val: Объект строки из которого будет получен объект int | float | None.
#     :return: Если строка val является целым числом, возвращает int(val).
#              Если строка val является числом с точкой, у которого после точки стоит
#              одна единственная целая цифра от 1 до 9, функция вернёт float(val).
#              Иначе возвращает None.
#
#     Примеры
#     --------
#     >>> get_int_or_float("1")
#     1
#     >>> get_int_or_float("2.1")
#     2.1
#     >>> get_int_or_float("3.2")
#     3.2
#     >>> get_int_or_float("4.45")
#     None
#     >>> get_int_or_float("abracadabra")
#     None
#
#     """
#     if isinstance(val, (int, float)):
#         return val
#     if not isinstance(val, str):
#         return None
#     if val.isdigit():
#         return int(val)
#     else:
#         assumption_is_float = val.split('.')
#         if len(assumption_is_float) != 2:
#             return None
#         before_dot, after_dot = assumption_is_float
#         if len(after_dot) != 1 or not after_dot.isdigit() or not before_dot.isdigit():
#             return None
#         return float(val)


def gen_int_or_float(data: Iterable[str]) -> tuple[MutableSequence[str], MutableSequence[int | float]]:
    good_vals: MutableSequence[int | float] = []
    bad_vals: MutableSequence[str] = []
    for el in data:
        val = get_int_or_float(el)
        if val is None:
            bad_vals.append(el)
        else:
            assert el == str(val)
            good_vals.append(val)
    return bad_vals, good_vals


def get_max_num_or_curr_val(curr_val: int | float, for_comparison: int | float | Iterable[int | float]):
    try:
        if isinstance(for_comparison, Iterable):
            return max(curr_val, max(for_comparison))
        return max(curr_val, for_comparison)
    except ValueError:
        return curr_val


def get_pretty_string(data: Iterable[Message]):
    return '; '.join((f'{i}) {msg.text_is_valid}' for i, msg in enumerate(data, 1)))



if __name__ == '__main__':
    pass


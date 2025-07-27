import operator
from collections.abc import (
    MutableMapping, Collection, MutableSequence, Iterable, Sequence, Container, MutableSet
)
from dataclasses import (
    dataclass,
    field
)
from typing import (
    TypeAlias,
    Type, TypeVar,
)

from sdp_lib.passport.constants import StagesMapping


Numbers = int | float
NumbersContainer = TypeVar('NumbersContainer', tuple, list, set, frozenset)


def get_int_or_float(num_as_str: str):
    if isinstance(num_as_str, (int, float)):
        num_as_str = str(num_as_str)
    if not isinstance(num_as_str, str):
        raise TypeError()
    if num_as_str.isdigit():
        val = int(num_as_str)
    else:
        before_dot, after_dot = num_as_str.split('.')
        if len(after_dot) != 1 or not after_dot.isdigit():
            raise ValueError
        val = float(num_as_str)
    assert num_as_str == str(val)
    return val

def make_int_or_float_collection(
    data: Iterable[str],
    container_type: Type[NumbersContainer] = set
) -> NumbersContainer:
    try:
        result = container_type(get_int_or_float(el) for el in data)
    except (ValueError, TypeError):
        result = container_type()
    return result






if __name__ == '__main__':
    print(make_int_or_float_collection('1,2,3,6.7'.split(',')))
    print(make_int_or_float_collection('1,2,3,6.7'.split(','), container_type=tuple))


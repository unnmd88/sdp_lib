import re
from enum import (
    StrEnum,
    Enum
)


MATCHING_OPERATORS = {'|': 'or', '&': 'and', '-': 'or'}
ALLOWED_LEFT_EXTRA_CHARS = {'(': 'left'}
ALLOWED_RIGHT_EXTRA_CHARS = {')': 'right'}
ALLOWED_PARENS = ALLOWED_LEFT_EXTRA_CHARS | ALLOWED_RIGHT_EXTRA_CHARS


class FieldNames(StrEnum):
    """ Содержит имена полей для словаря."""

    errors = 'errors'
    result_condition = 'result_condition'


class ErrMessages(StrEnum):
    """ Содержит текстовое представление ошибок."""

    invalid_condition = 'Некорректное условие'


class Patterns(Enum):
    """ Шаблоны для парса регулярными выражениями. """

    allowed_chars = re.compile('[' + r'\d()\s,' + f'{"".join(MATCHING_OPERATORS)}'  + ']')
    func_range = re.compile(r'\d+' + f'[{"".join(MATCHING_OPERATORS)}]' + r'\d+')
    operators = re.compile(f'[{"".join(MATCHING_OPERATORS)}]')
    func_single = re.compile(r'\d+')
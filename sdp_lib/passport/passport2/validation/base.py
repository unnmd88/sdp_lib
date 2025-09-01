import re
from collections import defaultdict
from collections.abc import MutableSequence, MutableMapping

from sdp_lib.passport.passport2.base import add_record
from sdp_lib.passport.passport2.patterns import Patterns
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import dump_to_dict, remove_chars


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
    # None

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


class BaseCellValidationResult:

    __slots__ = ('value', 'is_checked', 'ok', 'errors', 'warnings')

    def __init__(self, value=None):
        self.value = value
        self.is_checked = False
        self.ok = None
        self.errors = []
        self.warnings = []

    def __repr__(self):
        attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'{self.__class__.__name__}({attrs})'

    def __bool__(self):
        return bool(self.ok)

    def set_value(self, value):
        self.value = value

    def set_is_checked(self, value: bool):
        self.is_checked = value

    def set_ok(self, value: bool):
        self.ok = value

    def add_errors(self, *args, skip_add_if_err_is_empty=True):
        return add_record(self.errors, args, skip_add_if_err_is_empty)

    def add_warnings(self, *args, skip_add_if_err_is_empty=True):
        return add_record(self.warnings, args, skip_add_if_err_is_empty)

    def dump(self):
        # return {attr: getattr(self, attr) for attr in self.__slots__}
        return dump_to_dict(self)


class DirectionsOrStagesCellValidationResult(BaseCellValidationResult):

    __slots__ = BaseCellValidationResult.__slots__ + ('is_always_red', 'is_empty', 'nums', 'bad_nums', 'doubles')

    def __init__(self, string: str):
        super().__init__(string)
        self.is_always_red: bool = False
        self.is_empty = False
        self.nums: MutableSequence = []
        self.bad_nums: MutableSequence = []
        self.doubles: MutableMapping = defaultdict(int)

    def compute_and_set_ok_attr(self) -> bool:
        self.ok = all(not obj for obj in (self.is_empty, self.bad_nums))
        return self.ok


class CheckListDirectionRow:

    __slots__ = ('num', 'stages', 'is_empty')

    def __init__(
            self,
            num: BaseCellValidationResult = None,
            stages: DirectionsOrStagesCellValidationResult = None,
            is_empty: bool = False

    ):
        self.num = num
        self.stages = stages
        self.is_empty = is_empty

    def allow_to_compare_stages(self):
        return self.num.ok and self.stages.ok

    def dump(self):
        res = {}
        for attr in self.__slots__:
            try:
                res[attr] = dump_to_dict(getattr(self, attr))
            except AttributeError:
                res[attr] = getattr(self, attr)
        return res


class CheckListTable:

    __slots__ = ('length_columns', 'min_num_rows', 'head_rows', 'data_rows')

    def __init__(
            self,
            length_columns: BaseCellValidationResult = None,
            min_num_rows: BaseCellValidationResult = None,
            head_rows: MutableSequence[CheckListDirectionRow] = None,
            data_rows: MutableSequence[CheckListDirectionRow] = None
    ):

        self.length_columns = length_columns
        self.min_num_rows: BaseCellValidationResult = min_num_rows
        self.head_rows = head_rows or []
        self.data_rows = data_rows or []

    def load_length_columns(self, instance: BaseCellValidationResult, replace_old=True):
        if self.length_columns and not replace_old:
            return
        self.length_columns = instance

    def load_min_num_rows(self, instance: BaseCellValidationResult, replace_old=True):
        if self.min_num_rows and not replace_old:
            return
        self.min_num_rows = instance

    def dump(self):
        res = {}
        for attr in self.__slots__:
            try:
                res[attr] = dump_to_dict(getattr(self, attr))
            except AttributeError:
                res[attr] = [a.dump() for a in getattr(self, attr)]
        return res


def check_directions_or_stages_string(
    string: str,
    sep=',',
    always_red_pattern: str | re.Pattern = Patterns.always_red.value
) -> DirectionsOrStagesCellValidationResult:
    string_without_spaces = remove_chars(string, ' ')
    if not isinstance(always_red_pattern, re.Pattern):
        always_red_pattern = re.compile(always_red_pattern)
    res = DirectionsOrStagesCellValidationResult(string_without_spaces)
    res.is_empty = (len(string_without_spaces) == 0)
    res.is_always_red = bool(re.search(always_red_pattern, string_without_spaces))
    if not res.is_always_red and not res.is_empty:
        split_string = string_without_spaces.split(sep)
        tmp_basket = set()
        for n in split_string:
            num = get_int_or_float(n)
            if num is None:
                res.bad_nums.append(n)
            else:
                res.nums.append(num)
            if num in tmp_basket:
                res.doubles[num or n] += 1
            else:
                tmp_basket.add(num)
    res.compute_and_set_ok_attr()
    res.is_checked = True
    if res.bad_nums:
        res.errors.append(Text.bad_nums(res.bad_nums))
    return res
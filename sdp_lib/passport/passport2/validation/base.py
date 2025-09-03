import re
from collections import defaultdict
from collections.abc import MutableSequence, MutableMapping, Iterable
from typing import NamedTuple, Any

from sdp_lib.passport.constants import Patterns
from sdp_lib.passport.passport2.base import MessageStorage
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import dump_to_dict, remove_chars, add_record, get_int_or_float


class BadValue(NamedTuple):
    pos: int
    val: Any
    expected: Any


class Doubles(NamedTuple):
    val: Any
    positions: MutableSequence[int]
    count: int



class HeadRowData(NamedTuple):
    bad_vals: MutableSequence
    doubles: MutableSequence


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


class ContentCellValidationResult(BaseCellValidationResult):

    __slots__ = BaseCellValidationResult.__slots__ + ('expected_val', )

    def __init__(self, value=None, expected_val=None):
        super().__init__(value)
        self.expected = expected_val

    def set_expected_val(self, val):
        self.expected = val


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


class CheckListHeadRow(NamedTuple):
    row: Iterable[str]
    pos: int
    bad_vals: MutableSequence[BadValue]
    doubles: MutableMapping[str, int]
    messages: MessageStorage


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
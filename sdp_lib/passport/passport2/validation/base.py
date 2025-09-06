import re
from collections import defaultdict
from collections.abc import MutableSequence, MutableMapping, Iterable, Sequence
from typing import NamedTuple, Any

from sdp_lib.passport.constants import Patterns
from sdp_lib.passport.passport2.base import MessageStorage
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import dump_to_dict, remove_chars, add_record


class Cell(NamedTuple):
    pos: int
    value: str | int | float
    expected: str
    error_message: str


class BaseValidationResult(NamedTuple):
    value: str | int | float
    errors: Sequence[str]
    warnings: Sequence[str]


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
            length_columns: Cell = None,
            num_rows: Cell = None,
            head_rows: MutableSequence[CheckListDirectionRow] = None,
            data_rows: MutableSequence[CheckListDirectionRow] = None
    ):

        self.length_columns = length_columns
        self.min_num_rows = num_rows
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
        res =  {
            'length_columns': self.length_columns._asdict(),
            'min_num_rows': self.min_num_rows._asdict(),
        }
        print(res)
        return res
        res = {}
        for attr in self.__slots__:
            try:
                res[attr] = dump_to_dict(getattr(self, attr))
            except AttributeError:
                # res[attr] = [a.dump() for a in getattr(self, attr)]
                res[attr] = [a._asdict() for a in getattr(self, attr)]
        return res


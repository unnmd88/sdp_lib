import itertools
import re
from collections import defaultdict
from collections.abc import MutableSequence, MutableMapping, Set, Sequence, Callable
from dataclasses import dataclass, field, asdict, fields

from docx import Document

from sdp_lib.passport.constants import TableNames
from sdp_lib.passport.passport2.base import add_record
from sdp_lib.passport.passport2.patterns import Patterns
from sdp_lib.passport.passport2.utils import dump_as_dict
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import remove_chars, to_json, timed


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
        return dump_as_dict(self)


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
                res[attr] = dump_as_dict(getattr(self, attr))
            except AttributeError:
                res[attr] = getattr(self, attr)
        return res


@dataclass
class CheckListTable:
    length_direction_table: BaseCellValidationResult = field(default_factory=BaseCellValidationResult)
    min_num_rows: BaseCellValidationResult = field(default_factory=BaseCellValidationResult)
    head_rows: MutableSequence[CheckListDirectionRow] = field(default_factory=list)
    data_rows: MutableSequence[CheckListDirectionRow] = field(default_factory=list)
    validation_functions: Sequence[Callable] = field(default_factory=tuple)

    def get_validation_mapping(self):
        return zip(dt_struct_validation_functions, (getattr(self, name.name) for name in fields(self)))

    def dump(self):

        return {
            'length_direction_table': self.length_direction_table.dump(),
            'min_num_rows': self.min_num_rows.dump(),
            'head_rows': [m.dump() for m in self.head_rows],
            'data_rows': [m.dump() for m in self.data_rows],
        }


def check_directions_or_stages_string(
    string: str,
    sep=',',
    always_red_pattern: str | re.Pattern = Patterns.always_red.value
) -> DirectionsOrStagesCellValidationResult:
    string_without_spaces = remove_chars(string, ' ')
    if not isinstance(always_red_pattern, re.Pattern):
        always_red_pattern = re.compile(always_red_pattern)
    res = DirectionsOrStagesCellValidationResult(string_without_spaces)
    res.is_empty = len(string_without_spaces) == 0
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


def check_length_cols_direction_table(t_rows) -> str:
    if not len(t_rows[0].cells) in (14, 15):
        return Text.bad_length(TableNames.directions_table, len(t_rows[1]))
    return ''


def check_min_num_rows(t_rows) -> str:
    if len(t_rows) >= 3:
        return ''
    return Text.bad_num_rows(str(TableNames.directions_table), len(t_rows), 'мин=3')


def check_num_direction_or_stage(value) -> str:
    if get_int_or_float(value) is None:
        return f'Недопустимый номер: {value}' if value else f'Номер не задан'
    return ''


dt_struct_validation_functions: Sequence[Callable] = (check_length_cols_direction_table, check_min_num_rows)


@timed
def validate_directions_table(rows_cells) -> CheckListTable:
    check_list = CheckListTable(validation_functions=dt_struct_validation_functions)
    for func, validation_instance in check_list.get_validation_mapping():
        validation_instance: BaseCellValidationResult | CheckListDirectionRow
        err_msg = func(rows_cells)
        validation_instance.set_is_checked(True)
        validation_instance.set_ok(not bool(err_msg))
        validation_instance.add_errors(err_msg)
    for i in range(2, len(rows_cells)):
        cells = rows_cells[i].cells
        is_empty = all(not v.text for v in cells)
        num_from_cell = cells[0].text
        num_validation = BaseCellValidationResult(num_from_cell)
        num_validation.set_is_checked(True)
        err_num_msg = check_num_direction_or_stage(num_from_cell)
        num_validation.add_errors(err_num_msg)
        num_validation.set_ok(not bool(err_num_msg))
        stages = cells[2].text
        stages_validation = check_directions_or_stages_string(stages)
        stages_validation.set_is_checked(True)
        curr_row = CheckListDirectionRow(num_validation, check_directions_or_stages_string(stages), is_empty)
        check_list.data_rows.append(curr_row)
    print(to_json(check_list.dump(), 'ff'))
    return check_list


if __name__ == '__main__':
    strings = ('1,2,2,4', '1.1,1.4,5,7,10', '', '     ', '1e,2dqd')
    for s in strings:
        rr = check_directions_or_stages_string(s)

    # path = 'C://Programms//py.projects//sdp_lib//sdp_lib//passport//СО_2094_ул_Островитянова_ул_Ак_Волгина (2)'
    path = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_'
    doc = Document(f'{path}.docx')
    c = CheckListTable(validation_functions=dt_struct_validation_functions)
    validate_directions_table(doc.tables[0].rows)

    # sl = DirectionsOrStagesCellValidationResult('1,23')
    # tt = DirectionsOrStagesCellValidationResult('1,23')
    # print(to_json(dump_as_dict(tt)))

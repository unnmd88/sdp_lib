import re
from collections import Counter
from dataclasses import dataclass, field
from functools import cached_property
from os.path import split
from typing import NamedTuple
from collections.abc import (
    MutableMapping,
    Iterable, MutableSequence, Collection, Sequence, Generator
)
from typing import (
    Any,
    TypeVar,
    TypeAlias
)

from sdp_lib.passport.constants import (
    ColNamesDirectionsTable,
    StorageNames,
    ColNamesTimeProgramsTable,
    StagesMapping,
    TableNames,
    DirectionTypes,
    RowNames
)
from sdp_lib.passport.mixins import ReprMixin
from sdp_lib.passport.storages import (
    MessageStorage,
    add_record,
    Message,
    Actions,
    StagesData
)
from sdp_lib.passport.text_messages import Text
from sdp_lib.passport.utils import (
    get_int_or_float,
    gen_int_or_float
)
from sdp_lib.utils_common.utils_common import remove_chars


class CellData(NamedTuple):
    col_name: ColNamesDirectionsTable | ColNamesTimeProgramsTable | str
    init_val: Any
    default_val: Any
    value: Any
    is_valid: bool = True


class AbstractRow:

    row_name: RowNames

    def __init__(self):
        self._err_and_warn = MessageStorage()
        self._actions = Actions(row_name=self.row_name)

    def get_message_storage(self):
        return self._err_and_warn

    @property
    def allow_for_compare_stages(self) -> bool:
        return  self._actions.allow_compare_stages


T_Row = TypeVar('T_Row', bound=AbstractRow)


class AbstractTable:
    """ Абстрактный базовый класс таблицы паспорта. """

    table_name: TableNames = ''
    allowed_cnt_row_props: set
    row_class: Any

    def __init__(self, income_data: str):
        self._err_and_warn = MessageStorage()
        self._raw_data = income_data
        self._income_data_errors = MessageStorage(StorageNames.income_data)
        if self.table_name == TableNames.directions_table:
            self._stages_data = StageOrDirectionData(StagesMapping.direction_to_stages)
        elif self.table_name == TableNames.time_program:
            self._stages_data = StageOrDirectionData(StagesMapping.stage_to_direction)
        else:
            self._stages_data = None
        self._check_raw_data()
        self._rows: MutableMapping[float, T_Row] = {}
        self._rows_with_errors: MutableMapping[float, T_Row] = {}
        self._build()

    def _build(self):
        self._err_and_warn.clear_all()
        rows = self._raw_data.rstrip().split('\n')
        print(f'rows: {rows}')
        if len(rows) <= 1:
            self._err_and_warn.add_errors(Message(Text.income_table_text_rule))
            return
        for i, string_data in enumerate(rows):
            row_properties = remove_chars(string_data, ' ').split()
            if len(row_properties) not in self.allowed_cnt_row_props:
                self._err_and_warn.add_errors(Message(Text.income_table_text_rule))
                return
            elif len(row_properties) == 14 and self.table_name == TableNames.directions_table:
                t_zz = 0
                row_properties = [p if i != 10 else t_zz for i, p in enumerate(row_properties)]
            elif len(row_properties) == 1:
                if self.table_name == TableNames.directions_table:
                    num, direction_type, stages = str(i + 1), DirectionTypes.common, row_properties[0]
                    row_properties = [num, direction_type, stages]
            elif len(row_properties) == 2 and self.table_name == TableNames.time_program:
                num_pp, num_stage, directions,  = i + 1, row_properties[0], row_properties[1]
                row_properties = [num_pp, num_stage, directions]

            instance = self.row_class(i, *row_properties)
            # print(f'instance: {instance.stages}')
            # pprint.pprint(f'instance: {instance}')
            if instance.number.is_valid:
                key = instance.number.value
                self._load_row((key, instance))
            else:
                key = instance.number.init_val
                self._load_row_with_err((key, instance))

        if self.allow_to_compare_stages:
            if self.table_name == TableNames.directions_table:
                self._stages_data.refresh({d.number.value: d.stages.numbers for d in self._rows.values()})
            elif self.table_name == TableNames.time_program:
                self._stages_data.refresh({d.number.value: d.directions.numbers for d in self._rows.values()})

    def _check_raw_data(self) -> bool:
        """
        Проверяет валидность атрибута self._income_data
        :return: True если входные данные валидны для обработки, иначе False.
        """
        if len(self._raw_data) < 4:
            self._income_data_errors.add_errors(
                Message(f'Некорректные данные для обработки и формирования таблицы {self.table_name}')
            )
        return self.income_data_is_valid

    def _load_row(self, *args: tuple[float, T_Row]) -> int:
        """
         Добавляет пару ключ-значение в атрибут self._rows.
        :param args: Каждый элемент args - кортеж из 2 элементов, у которого 0 элемент - ключ, а 1 - значение.
        :return: Количество добавленных пар в self._rows
        """
        return add_record(self._rows, args)

    def _load_row_with_err(self, *args: tuple[float, T_Row]):
        """
         Добавляет пару ключ-значение в атрибут self._rows_with_errors.
        :param args: Каждый элемент args - кортеж из 2 элементов, у которого 0 элемент - ключ, а 1 - значение.
        :return: Количество добавленных пар в self._rows_with_errors
        """
        return add_record(self._rows_with_errors, args)

    def get_message_storage(self):
        return self._err_and_warn

    def get_income_data(self):
        """ Возвращает входные данные. """
        return self._raw_data

    @property
    def income_data_is_valid(self) -> bool:
        return not self._income_data_errors.errors

    def get_rows_with_errors(self) -> MutableMapping[float, T_Row]:
        return self._rows_with_errors

    def get_all_rows(self) -> MutableMapping[float, T_Row]:
        return self._rows

    @cached_property
    def allow_to_compare_stages(self) -> bool:
        return self._stages_data and all(instance.allow_for_compare_stages is True for instance in self._rows.values())

    def get_stages_data(self) -> StagesData | None:
        return self._stages_data


stages_content_type: TypeAlias = MutableMapping[float, set[float]]


# @dataclass(slots=True, frozen=True)
# class StagesData:
#     column_data: CellData
#     is_red: bool
#     allow_to_compare: bool
#     container: Collection[int | float]
#     bad_vals: MutableSequence[str]
#     doubles: Iterable[int | float]


class StageOrDirectionData(ReprMixin):

    common_always_red_pattern = re.compile(r'кр|покоя|крас', re.IGNORECASE)

    def __init__(
            self,
            stages_or_directions_string: str,
            entity: RowNames,
            sep: str = ',',
            always_red_pattern: str | re.Pattern = ''
    ):
        self._errors_and_warnings = MessageStorage()
        if isinstance(stages_or_directions_string, str):
            self._stages_or_directions = remove_chars(stages_or_directions_string, ' ')
        else:
            raise TypeError(f'{stages_or_directions_string!r} must be a str')
        self._entity = entity
        self._sep = sep
        if not always_red_pattern:
            pattern = self.common_always_red_pattern
        elif isinstance(always_red_pattern, re.Pattern):
            pattern = always_red_pattern
        elif isinstance(always_red_pattern, str):
            pattern = re.compile(always_red_pattern)
        else:
            raise ValueError(f'attr always_red_pattern must be a str or re.Pattern')
        self._is_always_red = bool(re.findall(pattern, self._stages_or_directions))
        self._process_income_data()


    def _process_income_data(self):
        numbers, self._doubles, self._bad_nums = [], {}, []
        self._numbers = set()
        unique_nums = set()
        nums_as_str = self._stages_or_directions.split(self._sep)
        if self._is_always_red:
            return
        more_than_one_sep_char_in_stages_or_directions_string = False
        for number in nums_as_str:
            number_as_int_or_float = get_int_or_float(number)
            if number_as_int_or_float is None:
                if number == '':
                    more_than_one_sep_char_in_stages_or_directions_string = True
                else:
                    self._bad_nums.append(number)
            else:
                if number_as_int_or_float in unique_nums:
                    self._doubles[number_as_int_or_float] = self._doubles.get(number_as_int_or_float, 0) + 1
                numbers.append(number_as_int_or_float)
                unique_nums.add(number_as_int_or_float)
        if self._entity == RowNames.direction:
            entity = ' направлений'
        elif self._entity == RowNames.stage:
            entity = ' фаз'
        else:
            entity = ''
        if self._sep.join(str(num) for num in numbers) != self._stages_or_directions:
            if more_than_one_sep_char_in_stages_or_directions_string:
                self._errors_and_warnings.errors += self._get_sep_errors()
            self._errors_and_warnings.errors += (Message(f'Недопустимый номер: {num}') for num in self._bad_nums)
        if self._errors_and_warnings.errors:
            errors = (f'{i}) {msg.text}' for i, msg in enumerate(self._errors_and_warnings.errors, 1))
            err_text = f'Найдены ошибки в строке{entity}: {"; ".join(errors)}'
        else:
            err_text = ''
        self._err_message = Message(err_text)
        if self._err_message.text:
            for storage in (self._numbers, self._doubles):
                storage.clear()

    def _get_sep_errors(self) -> Generator[Message, Any, None]:
        if self._stages_or_directions[-1] == self._sep:
            yield Message(f'Строка должна заканчиваться номером, а не разделителем "{self._sep}"')
        more_than_one_sep_char_in_string = re.findall(self._sep + r'{2,}', self._stages_or_directions )
        if more_than_one_sep_char_in_string:
            yield Message(f'Найдено более одного разделяющего символа "{self._sep}" подряд.')

    def get_bad_vals(self) -> Sequence[str]:
        return self._bad_nums

    def get_numbers_as_int_or_float(self) -> set[str]:
        return self._numbers

    def get_doubles(self) -> MutableMapping[int | float, int]:
        return self._doubles



def get_number(
    init_val: str | int | float,
    name: ColNamesTimeProgramsTable | ColNamesDirectionsTable
) -> CellData:
    default_val, is_valid = None, True
    try:
        val = get_int_or_float(init_val)
    except (ValueError, TypeError):
        is_valid = False
        val = init_val
    return CellData(name, init_val, default_val, val, is_valid)


# def get_stage_or_direction_data(
#         string_data: Any,
#         red_pattern: re.Pattern,
#         name: ColNamesTimeProgramsTable | ColNamesDirectionsTable
# ) -> StagesAndDirections:
#     default_val, is_valid, is_red, allow_to_compare, doubles = '', True, False, True, {}
#     try:
#         processed_string_data = remove_chars(string_data, ' ')
#         collection_as_str = processed_string_data.split(',')
#         collection_as_int_or_float = frozenset(gen_int_or_float(collection_as_str))
#         if not collection_as_int_or_float:
#             if re.findall(red_pattern, processed_string_data): # Если тип фазы "Фаза покоя"/"Пост. красн"
#                 is_red = True
#             else:
#                 raise ValueError
#         else:
#             if len(collection_as_str) != len(collection_as_int_or_float):
#                 cnt = Counter(make_int_or_float_collection(collection_as_str, list))
#                 doubles = {k: v for k, v in cnt.items() if v > 1}
#     except (TypeError, ValueError):
#         allow_to_compare = False
#         is_valid = False
#         collection_as_int_or_float = frozenset()
#         doubles = {}
#     return StagesAndDirections(
#         ColumnData(name, string_data, default_val, string_data, is_valid),
#         is_red,
#         allow_to_compare,
#         collection_as_int_or_float,
#         doubles
#     )


def get_stage_or_direction_data(
        string_data: Any,
        red_pattern: re.Pattern,
        name: ColNamesTimeProgramsTable | ColNamesDirectionsTable
) -> StageOrDirectionData:

    default_val = ''
    is_valid = True
    is_red = False
    allow_to_compare = True
    collection_as_int_or_float = None
    doubles = {}

    processed_string_data = remove_chars(string_data, ' ')
    collection_as_str = processed_string_data.split(',')
    bad_vals, good_vals = gen_int_or_float(collection_as_str)
    if len(bad_vals) == 1 and re.findall(red_pattern, processed_string_data):# Если тип фазы/направления = "Фаза покоя"/"Пост. красн"
        is_red = True
        bad_vals.clear()
    elif not bad_vals:
        collection_as_int_or_float = frozenset(good_vals)
        if len(collection_as_str) != len(collection_as_int_or_float):
            cnt = Counter(good_vals)
            doubles = {k: v for k, v in cnt.items() if v > 1}
        is_valid = True
    else:
        is_valid = allow_to_compare = False
    return StageOrDirectionData(
        CellData(name, string_data, default_val, string_data, is_valid),
        is_red,
        allow_to_compare,
        collection_as_int_or_float or frozenset(),
        bad_vals,
        doubles
    )


def get_column_data_instance(name: str, init_val: Any, default_val=None, is_valid: bool = True) -> CellData:
    return CellData(name, init_val, default_val, init_val or default_val, is_valid)


if __name__ == '__main__':

    stages = StageOrDirectionData('1,2,3,,4,3,', RowNames.stage)
    print(stages)

    stages2 = StageOrDirectionData('пост. кр', RowNames.stage)
    print(stages2)

    stages3 = StageOrDirectionData('1ю3ю4.4,', RowNames.stage)
    print(stages3)


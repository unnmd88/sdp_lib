import logging
import re
from dataclasses import dataclass, field
from functools import cached_property
from typing import NamedTuple
from collections.abc import (
    MutableMapping,
    Iterable,
    Sequence,
    Generator, Mapping, Set
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
from sdp_lib.passport.utils import get_int_or_float
from sdp_lib.utils_common.utils_common import remove_chars
from sdp_lib.passport import logging_config


logger = logging.getLogger('full_log')


class Cell(NamedTuple):
    name: ColNamesDirectionsTable | ColNamesTimeProgramsTable | str
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
            self._stages_data = StageOrDirectionCell(StagesMapping.direction_to_stages)
        elif self.table_name == TableNames.time_program:
            self._stages_data = StageOrDirectionCell(StagesMapping.stage_to_direction)
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


class StageOrDirectionCell(ReprMixin):

    common_always_red_pattern = re.compile(r'кр|покоя|крас', re.IGNORECASE)

    def __init__(
            self,
            number: int | float,
            entity: RowNames,

            stages_or_directions_string: str,
            sep: str = ',',
            always_red_pattern: str | re.Pattern = ''
    ):
        self._errors_and_warnings = MessageStorage()
        if isinstance(stages_or_directions_string, str):
            self._stages_or_directions = remove_chars(stages_or_directions_string, ' ')
        else:
            raise TypeError(f'{stages_or_directions_string!r} must be a str')
        self._number = number
        self._entity = entity
        self._sep = sep
        self._is_always_red = bool(
            re.findall(self._get_always_red_pattern(always_red_pattern), self._stages_or_directions)
        )
        self._process_income_data()
        if self._entity == RowNames.direction:
            self._cell_name = ColNamesDirectionsTable.stages
        elif self._entity == RowNames.stage:
            self._cell_name = ColNamesTimeProgramsTable.directions
        else:
            self._cell_name = ''
        logger.info(self)

    def _get_always_red_pattern(self, income_data: str | re.Pattern) -> re.Pattern:
        if not income_data:
            pattern = self.common_always_red_pattern
        elif isinstance(income_data, re.Pattern):
            pattern = income_data
        elif isinstance(income_data, str):
            pattern = re.compile(income_data)
        else:
            raise ValueError(f'attr always_red_pattern must be a str or re.Pattern')
        return pattern

    def _process_income_data(self):
        self._numbers, self._doubles, self._bad_nums = frozenset(), {}, []
        if self._is_always_red:
            return
        if self._errors_and_warnings.add_errors(*self._get_sep_errors()) > 0:
            return
        nums_as_str = self._stages_or_directions.split(self._sep)
        numbers, unique_nums = [], set()
        for number in nums_as_str:
            number_as_int_or_float = get_int_or_float(number)
            if number_as_int_or_float is None:
                self._bad_nums.append(number)
            else:
                if number_as_int_or_float in unique_nums:
                    self._doubles[number_as_int_or_float] = self._doubles.get(number_as_int_or_float, 0) + 1
                numbers.append(number_as_int_or_float)
                unique_nums.add(number_as_int_or_float)
        if self._bad_nums:
            self._errors_and_warnings.add_errors(*(Message(f'Недопустимый номер: {num}') for num in self._bad_nums))
        try:
            assert self._sep.join(str(num) for num in numbers) == self._stages_or_directions
        except AssertionError:
            logger.critical(self._create_text_error_in_generation_numbers(numbers))
            raise
        self._numbers = frozenset(unique_nums)

    def _create_text_error_in_generation_numbers(self, numbers: Iterable[int | float]) -> str:
        generated_numbers = 'Сгенерированные номера:'
        income_numbers = 'Входная строка с номерами:'
        indent = max(len(generated_numbers), len(income_numbers))
        return (
            f'Программная ошибка логики: сгенерированные номера не должны различаться со входными:\n'
            f'{generated_numbers:<{indent}} {self._sep.join(str(num) for num in numbers)}\n'
            f'{income_numbers:<{indent}} {self._stages_or_directions}\n'
            f'{self}'
        )

    def _get_sep_errors(self) -> Generator[Message, Any, None]:
        if self._stages_or_directions[-1] == self._sep:
            yield Message(f'Строка не должна заканчиваться разделителем "{self._sep}"')
        more_than_one_sep_char_in_string = re.findall(self._sep + r'{2,}', self._stages_or_directions )
        if more_than_one_sep_char_in_string:
            yield Message(f'Найдено более одного разделяющего символа "{self._sep}" подряд.')

    # def _get_err_text(self) -> str:
    #     if self._errors_and_warnings.errors:
    #         if self._entity == RowNames.direction:
    #             cell_name = f' {ColNamesDirectionsTable.stages}'
    #             entity = ' направления'
    #         elif self._entity == RowNames.stage:
    #             cell_name = f' {ColNamesTimeProgramsTable.directions}'
    #             entity = ' фазы'
    #         else:
    #             cell_name = entity =  ''
    #         errors = (f'{i}) {msg.text}' for i, msg in enumerate(self._errors_and_warnings.errors, 1))
    #         err_text = f'Найдены ошибки: направления {self.entity_number} {entity} в колонке{cell_name}: {"; ".join(errors)}'
    #     else:
    #         err_text = ''
    #     return err_text
    #
    # def _get_warn_text(self) -> str:
    #     if self._errors_and_warnings.warnings:
    #         warnings = (f'{i}) {msg.text}' for i, msg in enumerate(self._errors_and_warnings.errors, 1))
    #         warnings_text = f'Предупреждения: {"; ".join(warnings)}'
    #     else:
    #         warnings_text = ''
    #     return warnings_text

    def get_errors(self):
        return self._errors_and_warnings.errors

    def get_bad_vals(self) -> Sequence[str]:
        return self._bad_nums

    def get_numbers_as_int_or_float(self) -> Set[str]:
        return self._numbers

    def get_doubles(self) -> MutableMapping[int | float, int]:
        return self._doubles

    def get_errors_as_pretty_string(self):
        errors = '; '.join((f'{i}) {msg.text}' for i, msg in enumerate(self._errors_and_warnings.errors, 1)))
        return f'Найдены ошибки. {str(self._entity)}={self._number}: {errors}'

    @property
    def is_valid(self):
        return True if not self._errors_and_warnings.errors else False

    @property
    def is_always_red(self) -> bool:
        return self._is_always_red


def get_number_data(
    init_val: str | int | float,
    name: ColNamesTimeProgramsTable | ColNamesDirectionsTable
) -> Cell:
    default_val, is_valid = None, True
    try:
        val = get_int_or_float(init_val)
    except (ValueError, TypeError):
        is_valid = False
        val = None
    return Cell(name, init_val, default_val, val, is_valid)
#
#
# def get_stage_or_direction_data(
#         string_data: Any,
#         red_pattern: re.Pattern,
#         name: ColNamesTimeProgramsTable | ColNamesDirectionsTable
# ) -> StageOrDirectionData:
#
#     default_val = ''
#     is_valid = True
#     is_red = False
#     allow_to_compare = True
#     collection_as_int_or_float = None
#     doubles = {}
#
#     processed_string_data = remove_chars(string_data, ' ')
#     collection_as_str = processed_string_data.split(',')
#     bad_vals, good_vals = gen_int_or_float(collection_as_str)
#     if len(bad_vals) == 1 and re.findall(red_pattern, processed_string_data):# Если тип фазы/направления = "Фаза покоя"/"Пост. красн"
#         is_red = True
#         bad_vals.clear()
#     elif not bad_vals:
#         collection_as_int_or_float = frozenset(good_vals)
#         if len(collection_as_str) != len(collection_as_int_or_float):
#             cnt = Counter(good_vals)
#             doubles = {k: v for k, v in cnt.items() if v > 1}
#         is_valid = True
#     else:
#         is_valid = allow_to_compare = False
#     return StageOrDirectionData(
#         CellData(name, string_data, default_val, string_data, is_valid),
#         is_red,
#         allow_to_compare,
#         collection_as_int_or_float or frozenset(),
#         bad_vals,
#         doubles
#     )
#
#
# def get_column_data_instance(name: str, init_val: Any, default_val=None, is_valid: bool = True) -> CellData:
#     return CellData(name, init_val, default_val, init_val or default_val, is_valid)


if __name__ == '__main__':

    stages = StageOrDirectionCell(1, RowNames.direction, '1,2,3,,4,3,')
    print(stages)

    stages2 = StageOrDirectionCell(1, RowNames.direction, 'пост. кр')
    print(stages2)

    stages3 = StageOrDirectionCell(1, RowNames.direction, '1ю3ю4.4,')
    print(stages3)

    stages4 = StageOrDirectionCell(1, RowNames.direction, '1,2,7, 8.2 ')
    print(stages4)
    print(stages4.is_valid)
    for k, v in stages4.__dict__.items():
        print(f'{k}={v}')
    print(stages.is_valid)
    print(stages.get_errors_as_pretty_string())
    print(stages.get_errors())



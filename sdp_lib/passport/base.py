import re
from collections import Counter
from dataclasses import dataclass, field
from typing import NamedTuple
from abc import abstractmethod
from collections.abc import (
    MutableSequence,
    MutableMapping,
    Iterable
)
from typing import Any, TypeVar, TypeAlias

from sdp_lib.passport.constants import (
    ColNamesDirectionsTable,
    StorageNames, ColNamesTimeProgramsTable, StagesMapping
)
from sdp_lib.passport.storages import (
    MessageStorage,
    add_record,
    Message
)
from sdp_lib.passport.utils import make_int_or_float_collection, get_int_or_float
from sdp_lib.utils_common.utils_common import remove_chars


# class ColumnValues:
#     __slots__ = ('_col_name', '_init_val', '_default_val', '_value')
#
#     def __init__(
#             self,
#             col_name: ColNamesDirectionsTable | ColNamesTimeProgramsTable,
#             init_val: Any,
#             default_val: Any,
#             value: Any
#     ):
#         self._col_name = col_name
#         self._init_val = init_val
#         self._default_val = default_val
#         self._value = value
#
#     def __repr__(self):
#         attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
#         return f'{self.__class__.__name__}({attrs})'
#
#     @property
#     def col_name(self):
#         return self._col_name
#
#     @property
#     def init_val(self):
#         return self._init_val
#
#     @property
#     def default_val(self):
#         return self._default_val
#
#     @property
#     def value(self):
#         return self._value
#
#     def set_value(self, value):
#         self._value = value


class ColumnData(NamedTuple):
    col_name: ColNamesDirectionsTable | ColNamesTimeProgramsTable | str
    init_val: Any
    default_val: Any
    value: Any
    is_valid: bool = True


class AbstractEntity:
    """ Абстрактный базовый класс элемента паспорта(строка, таблица и т.д.) """

    def __init__(self):
        self._err_and_warn = MessageStorage()

    def get_message_storage(self):
        return self._err_and_warn

    def _get_common_val(self, init_val, name: str, default_val=None) -> ColumnData:
        return ColumnData(ColNamesDirectionsTable.stages, init_val, default_val, init_val or default_val)


T_Row = TypeVar('T_Row', bound=AbstractEntity)


class AbstractTable(AbstractEntity):
    """ Абстрактный базовый класс таблицы паспорта. """

    table_name: str = ''

    def __init__(self, income_data: str):
        super().__init__()
        self._raw_data = income_data
        self._income_data_errors = MessageStorage(StorageNames.income_data)
        self._check_raw_data()
        self._rows: MutableMapping[float, T_Row] = {}
        self._rows_with_errors: MutableMapping[float, T_Row] = {}

    @abstractmethod
    def _create_data_from_income_string(self):
        """ Основной метод создания данных для таблицы. """
        ...

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


stages_content_type: TypeAlias = MutableMapping[float, set[float]]


@dataclass(slots=True, frozen=True)
class StagesAndDirections:
    column_data: ColumnData
    is_red: bool
    allow_to_compare: bool
    container: frozenset[int | float]
    doubles: Iterable[int | float]


def get_number(
    init_val: str | int | float,
    name: ColNamesTimeProgramsTable | ColNamesDirectionsTable
) -> ColumnData:
    default_val, is_valid = None, True
    try:
        val = get_int_or_float(init_val)
    except (ValueError, TypeError):
        is_valid = False
        val = init_val
    return ColumnData(name, init_val, default_val, val, is_valid)


def get_stage_or_direction_data(
        string_data: Any,
        red_pattern: re.Pattern,
        name: ColNamesTimeProgramsTable | ColNamesDirectionsTable
) -> StagesAndDirections:
    default_val, is_valid, is_red, allow_to_compare, doubles = '', True, False, True, {}
    try:
        processed_string_data = remove_chars(string_data, ' ')
        collection_as_str = processed_string_data.split(',')
        collection_as_int_or_float: frozenset[float | int] = make_int_or_float_collection(
            collection_as_str, frozenset
        )
        if not collection_as_int_or_float:
            if re.findall(red_pattern, processed_string_data): # Если тип фазы "Фаза покоя"/"Пост. красн"
                is_red = True
            else:
                raise ValueError
        else:
            if len(collection_as_str) != len(collection_as_int_or_float):
                cnt = Counter(make_int_or_float_collection(collection_as_str, list))
                doubles = {k: v for k, v in cnt.items() if v > 1}
    except (TypeError, ValueError):
        allow_to_compare = False
        is_valid = False
        collection_as_int_or_float = frozenset()
        doubles = {}
    return StagesAndDirections(
        ColumnData(name, string_data, default_val, string_data, is_valid),
        is_red,
        allow_to_compare,
        collection_as_int_or_float,
        doubles
    )


def get_column_data_instance(name: str, init_val: Any, default_val=None, is_valid: bool = True) -> ColumnData:
    return ColumnData(name, init_val, default_val, init_val or default_val, is_valid)


if __name__ == '__main__':

    o = get_number(0, ColNamesTimeProgramsTable.directions)
    print(o)



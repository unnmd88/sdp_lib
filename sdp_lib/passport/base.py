import typing
from abc import abstractmethod
from collections.abc import (
    MutableSequence,
    MutableMapping,
    Iterable
)
from typing import Any, TypeVar

from sdp_lib.passport.constants import ColNamesDirectionsTable, StorageNames
from sdp_lib.passport.mixins import ReprMixin
from sdp_lib.passport.storages import MessageStorage, add_record, Message


class AbstractEntity:
    def __init__(self):
        self._err_and_warn = MessageStorage()

    def get_message_storage(self):
        return self._err_and_warn



# class AbstractRow:
#     def __init__(self):
#         self._errors = []
#         self._warnings = []
#
#     def add_errors(self, *errors: str):
#         return add_record(self._errors, errors)
#
#     def add_warnings(self, *warnings: str):
#         return add_record(self._errors, warnings)
#
#     def get_errors(self) -> MutableSequence[str]:
#         return self._errors
#
#     def get_warnings(self) -> MutableSequence[str]:
#         return self._warnings
#
#     @property
#     def is_valid(self) -> bool:
#         return not bool(self._errors)


T_Row = TypeVar('T_Row', bound=AbstractEntity)


class ColumnValues:
    __slots__ = ('_col_name', '_init_val', '_default_val', '_value')

    def __init__(
            self,
            col_name: ColNamesDirectionsTable,
            init_val: Any,
            default_val: Any,
            value: Any
    ):
        self._col_name = col_name
        self._init_val = init_val
        self._default_val = default_val
        self._value = value

    def __repr__(self):
        attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'{self.__class__.__name__}({attrs})'

    @property
    def col_name(self):
        return self._col_name

    @property
    def init_val(self):
        return self._init_val

    @property
    def default_val(self):
        return self._default_val

    @property
    def value(self):
        return self._value

    def set_value(self, value):
        self._value = value


class AbstractTable(AbstractEntity):

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
        if len(self._raw_data) < 4:
            self._income_data_errors.add_errors(
                Message(f'Некорректные данные для обработки и формирования таблицы {self.table_name}')
            )
        return self.income_data_is_valid

    def _load_row(self, *args: tuple[float, T_Row]):
        return add_record(self._rows, args)

    def _load_row_with_err(self, *args: tuple[float, T_Row]):
        return add_record(self._rows_with_errors, args)

    def get_income_data(self):
        return self._raw_data

    @property
    def income_data_is_valid(self) -> bool:
        return not self._income_data_errors.errors

    def get_rows_with_errors(self) -> MutableMapping[float, T_Row]:
        return self._rows_with_errors

    def get_all_rows(self) -> MutableMapping[float, T_Row]:
        return self._rows


if __name__ == '__main__':
    o = AbstractEntity()
    print(o)
    cl = ColumnValues(ColNamesDirectionsTable.t_flashing_green, None, 3, 3)
    print(cl)



import inspect
import itertools
import logging
import re
from abc import abstractmethod
from collections import deque
from dataclasses import dataclass, field, asdict, astuple, fields
from functools import cached_property
from itertools import zip_longest, combinations_with_replacement
from typing import NamedTuple, TypeVar, Type
from collections.abc import (
    MutableMapping,
    Iterable,
    Sequence,
    Generator,
    Set, MutableSequence, Collection, Container
)
from typing import (
    Any,
    TypeAlias
)


from sdp_lib.passport.constants import (
    ColNamesDirectionsTable,
    StorageNames,
    ColNamesTimeProgramsTable,
    StagesMapping,
    TableNames,
    DirectionEntities,
    RowNames, MessageLevels, MessageCategories, Fields, categories_descriptions, ComparisonDescriptions, default_values
)
from sdp_lib.passport.mixins import ReprMixin, EntityNameMixin
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import remove_chars, get_arg_names, stages_as_string
from sdp_lib.passport import logging_config


logger = logging.getLogger('full_log')


stages_or_direction_num: TypeAlias = int | float
# stages_or_direction_container: TypeAlias = MutableMapping[stages_or_direction_num, Set[stages_or_direction_num]]
stages_or_direction_container: TypeAlias = MutableMapping[stages_or_direction_num, Set[stages_or_direction_num]]


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
    >>> get_int_or_float("1")
    1
    >>> get_int_or_float("2.1")
    2.1
    >>> get_int_or_float("3.2")
    3.2
    >>> get_int_or_float("4.45")
    None
    >>> get_int_or_float("abracadabra")
    None

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


class Message(NamedTuple):
    text: str
    category: MessageCategories | int
    level: MessageLevels = MessageLevels.debug


def add_record(
    container: MutableSequence | MutableMapping,
    records: Iterable[str | Message] | Iterable[tuple[float, Any]]
) -> int:
    cnt = 0
    if isinstance(container, MutableMapping):
        for key, row in records:
            cnt += 1
            container[key] = row
    elif isinstance(container, MutableSequence):
        for record in records:
            cnt += 1
            container.append(record)
    return cnt


class Cell(NamedTuple):
    cell_name: ColNamesDirectionsTable | ColNamesTimeProgramsTable | str
    init_val: Any
    default_val: Any
    value: Any
    is_valid: bool = True


def get_cell(
    name: str,
    init_val: Any,
    default_val=None,
    is_valid: bool = True
) -> Cell:
    return Cell(name, init_val, default_val, init_val or default_val, is_valid)


def get_cell_with_value_as_number_(
    init_val: str | int | float,
    name: ColNamesTimeProgramsTable | ColNamesDirectionsTable
) -> Cell:
    default_val, is_valid = None, True
    val = get_int_or_float(init_val)
    if val is None:
        is_valid = False
        val = init_val
    return Cell(name, init_val, default_val, val, is_valid)


def get_cell_with_value_as_prom_tact_time(direction_type: DirectionEntities, col_name: ColNamesDirectionsTable, init_val) -> Cell:
    default_val = default_values.get((direction_type, col_name))
    if init_val is None:
        val = default_val
    else:
        val = init_val
    return Cell(col_name, init_val, default_val, val)


def get_pretty_string(data: Iterable[Message]):
    return '; '.join((f'{i}) {msg.text}' for i, msg in enumerate(data, 1)))


compare_stages_entities = {RowNames.direction, RowNames.stage, TableNames.directions_table, TableNames.time_program}


class Permissions:

    __slots__ = (
        '_entity',
        '_compare_stages',
        '_permission_to_set_flag_from_false_to_true'
    )

    def __init__(self, entity: RowNames | TableNames = None):
        self.initialize(entity)

    def __repr__(self):
        attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'{self.__class__.__name__}({attrs})'

    def initialize(self, entity: RowNames | TableNames):
        self._entity = entity
        self._compare_stages = True if entity in compare_stages_entities else False
        self._permission_to_set_flag_from_false_to_true = False

    def set_permission_set_flag_from_false_to_true(self, value: bool):
        self._permission_to_set_flag_from_false_to_true = bool(value)

    def _check_permission_and_return_flag(self, flag: bool):
        flag = bool(flag)
        if not self._compare_stages and flag and self._permission_to_set_flag_from_false_to_true is False:
            # return False
            raise AttributeError("can't set attribute from False to True")
        return flag

    def set_val_for_compare_stages(self, flag: bool):
        self._compare_stages = self._check_permission_and_return_flag(flag)

    @property
    def compare_stages(self) -> bool:
        return self._compare_stages


@dataclass(slots=True)
class MessageStorage:

    name: str = ''
    errors: MutableSequence[Message] = field(default_factory=list)
    warnings: MutableSequence[Message] = field(default_factory=list)

    def set_name(self, name: str | StorageNames):
        self.name = name

    def add_errors(self, *errors: Message):
        return add_record(self.errors, errors)

    def add_warnings(self, *warnings: Message):
        return add_record(self.warnings, warnings)

    def clear_all(self):
        self.errors.clear()
        self.warnings.clear()

    def get_errors_by_categories(self, message_as_text=True):
        res = {}
        for msg in self.errors:
            m = msg.text if message_as_text else msg
            try:
                res[int(msg.category)][Fields.messages].append(m)
            except KeyError:
                cat, description = categories_descriptions.get(int(msg.category), (None, None))
                res[cat] = {
                    str(Fields.category_description): description,
                    str(Fields.messages): [m]
                }
        return res


class StagesData:

    __slots__ = (
        '_mapping_type',
        '_direction_to_stages_mapping',
        '_stage_to_direction_mapping',
    )

    def __init__(self, mapping_type: StagesMapping):
        self._mapping_type = mapping_type
        self._direction_to_stages_mapping: stages_or_direction_container = {}
        self._stage_to_direction_mapping: stages_or_direction_container = {}

    def __repr__(self):
        attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'{self.__class__.__name__}({attrs})'

    def __eq__(self, other) -> bool:
        if not isinstance(other, StagesData):
            return NotImplemented
        return (
                self._direction_to_stages_mapping == other.get_direction_to_stages_mapping()
                and
                self._stage_to_direction_mapping == other.get_stage_to_direction_mapping()
        )

    def build(
            self,
            data: stages_or_direction_container,
            gen_val_as_frozenset: bool = True,
            sort: bool = False
    ):
        if self._mapping_type == StagesMapping.direction_to_stages:
            container1, container2 = self._direction_to_stages_mapping, self._stage_to_direction_mapping
        elif self._mapping_type == StagesMapping.stage_to_direction:
            container1, container2 = self._stage_to_direction_mapping, self._direction_to_stages_mapping
        else:
            raise TypeError(
                f'Invalid mapping_type: {self._mapping_type!r}. Use mapping_type from class {StagesMapping!r}'
            )
        if len(container1) > 0:
            container1.clear()
        container1 |= {k: v for k, v in data.items()}
        if len(container2) > 0:
            container2.clear()
        for key, values in container1.items():
            for value in values:
                try:
                    container2[value].add(key)
                except KeyError:
                    container2[value] = {key}
        if gen_val_as_frozenset:
            self._gen_val_as_frozenset(container2)
        if sort:
            self._sort_container(container2)

    def _gen_val_as_frozenset(self, container: stages_or_direction_container) -> stages_or_direction_container:
        for k in container:
            fs = frozenset(container[k])
            container[k] = fs
        return container

    def _sort_container(
            self, container: stages_or_direction_container,
            key=None
    ) -> stages_or_direction_container:
        sorted_dict = {k: v for k, v in sorted(container.items(), key=key)}
        container.clear()
        container |= sorted_dict
        return container

    def get_direction_to_stages_mapping(self) -> stages_or_direction_container:
        return self._direction_to_stages_mapping

    def get_stage_to_direction_mapping(self):
        return self._stage_to_direction_mapping

    @property
    def max_stage(self) -> int | float:
        return max(self._stage_to_direction_mapping)

    @property
    def max_direction(self) -> int | float:
        return max(self._direction_to_stages_mapping)


@dataclass(slots=True, frozen=True)
class BaseEntityData:

    name: RowNames | TableNames
    permissions: Permissions = field(default_factory=Permissions)
    err_and_warn: MessageStorage = field(default_factory=MessageStorage)

    def __post_init__(self):
        self.permissions.initialize(entity=self.name)

    @property
    def allow_compare_stages(self) -> bool:
        return self.permissions.compare_stages

    @property
    def has_errors(self) -> bool:
        return bool(self.err_and_warn.errors)


class AbstractRow(EntityNameMixin):

    def __init__(self, index: int):
        self._extra_data = BaseEntityData(self.name)
        self.index = index
        self._cells = ... # instance of Dataclass

    def __iter__(self):
        instance = self._cells
        return (getattr(instance, field_name.name) for field_name in fields(instance))

    def __getitem__(self, item) -> Cell:
        return self._cells[item]

    def __len__(self):
        return len(self._cells)

    def __eq__(self, other):
        return self._cells == other

    def dump_to_dict(self):
        instance = self._cells
        chain = itertools.chain(
            ((str(Fields.index), self.index), ),
            ((field_name.name, getattr(instance, field_name.name).value) for field_name in fields(instance)),
            ((str(Fields.errors), self._extra_data.err_and_warn.get_errors_by_categories()),)
        )
        return {k: v for k, v in chain}

    @cached_property
    def extra_data(self) -> BaseEntityData:
        return self._extra_data

    @property
    def has_errors(self) -> bool:
        return self._extra_data.has_errors

    @property
    def cells(self):
        """ Возвращает экземпляр реализованного класса dataclass. """
        return self._cells

    def iter_cells(self):
        return iter(self)

    @property
    def allow_compare_stages(self) -> bool:
        return self._extra_data.permissions.compare_stages


TableRow = TypeVar('TableRow', bound=AbstractRow)


class AbstractTableWithStages(EntityNameMixin):
    """ Абстрактный базовый класс таблицы паспорта. """

    allowed_cnt_row_props: set
    row_class: Type[TableRow]
    key_name: str

    def __init__(self, income_data: str):
        super().__init__()
        self._extra_data = BaseEntityData(self.name)
        self._income_data = income_data
        self._income_data_errors = MessageStorage(StorageNames.income_data)
        if self.name == TableNames.directions_table:
            self._stages_data = StagesData(StagesMapping.direction_to_stages)
        elif self.name == TableNames.time_program:
            self._stages_data = StagesData(StagesMapping.stage_to_direction)
        else:
            self._stages_data = None
            raise ValueError(f'attr cls.name <{self.name}> is not allowed.')
        self._check_raw_data()
        self._rows: MutableSequence[TableRow] = []
        self._build()

    def __iter__(self):
        return (row for row in self._rows)

    def __getitem__(self, item):
        return self._rows[item]
        # return self._rows[item]

    def __eq__(self, other):
        return self._income_data == other

    def iter_rows(self) -> Generator[TableRow, Any, None]:
        """ Возвращает итератор по всем строкам таблицы. """
        return iter(self)

    def get_rows_data(self) -> MutableSequence[dict]:
        """
        Возвращает список из словарей, где каждый словарь - данные ячеек строки таблицы.
        Key в словаре - имя ячейки, а value - данные.
        """
        return [row.dump_to_dict() for row in self._rows]

    def dump_to_dict(self) -> dict:
        """ Возвращает словарь с данными всех таблицы. """
        return {
            str(Fields.income_data): {
                str(Fields.is_valid): self.income_data_is_valid,
                str(Fields.errors): self._income_data_errors.get_errors_by_categories(),
            },
            str(Fields.max_stage): self.get_max_stage(),
            str(Fields.max_direction): self.get_max_direction_num(),
            str(self.key_name): self.get_rows_data(),
        }

    def _build(self):
        """ Строит таблицу на основе self._income_data. """
        self._extra_data.err_and_warn.clear_all()
        rows = self._income_data.lstrip().rstrip().split('\n')
        if len(rows) <= 1:
            self._extra_data.err_and_warn.add_errors(Message(Text.income_table_text_rule, MessageCategories.validation))
            return
        for i, string_data in enumerate(rows):
            row_properties = remove_chars(string_data, ' ').split()
            if len(row_properties) not in self.allowed_cnt_row_props:
                self._extra_data.err_and_warn.add_errors(Message(Text.income_table_text_rule, MessageCategories.validation))
                return
            elif len(row_properties) == 14 and self.name == TableNames.directions_table:
                t_zz = 0
                row_properties = [p if i != 10 else t_zz for i, p in enumerate(row_properties)]
            elif len(row_properties) == 1:
                if self.name == TableNames.directions_table:
                    num, direction_type, stages = str(i + 1), DirectionEntities.common, row_properties[0]
                    row_properties = [num, direction_type, stages]
            elif len(row_properties) == 2 and self.name == TableNames.time_program:
                num_pp, num_stage, directions = i + 1, row_properties[0], row_properties[1]
                row_properties = [num_pp, num_stage, directions]
            _row = self.row_class(i, *row_properties)
            self._load_row(_row)
            if _row.has_errors:
                self._extra_data.permissions.set_val_for_compare_stages(False)
        if self._extra_data.permissions.compare_stages:
            self._extra_data.permissions.set_val_for_compare_stages(self._check_permission_for_compare_stages())
        self._load_data_to_stages_data()

    def _check_raw_data(self) -> bool:
        """
        Проверяет валидность атрибута self._income_data
        :return: True если входные данные валидны для обработки, иначе False.
        """
        if len(self._income_data) < 4:
            self._income_data_errors.add_errors(
                Message(f'Некорректные входные данные для обработки и формирования таблицы <{self.name}>', MessageCategories.validation)
            )
        return self.income_data_is_valid

    def _load_row(self, *args: tuple[float, Any]) -> int:
        """
         Добавляет пару ключ-значение в атрибут self._rows.
        :param args: Каждый элемент args - кортеж из 2 элементов, у которого 0 элемент - ключ, а 1 - значение.
        :return: Количество добавленных пар в self._rows
        """
        return add_record(self._rows, args)

    def _load_data_to_stages_data(self):
        if self._extra_data.allow_compare_stages:
            if self.name == TableNames.directions_table:
                self._stages_data.build({row.cells.number.value: row.cells.stages.get_numbers() for row in self._rows})
            elif self.name == TableNames.time_program:
                self._stages_data.build({row.cells.number.value: row.cells.directions.get_numbers() for row in self._rows})

    def _check_permission_for_compare_stages(self) -> bool:
        if self._stages_data is None or any(instance.allow_compare_stages is False for instance in self._rows):
            return False
        return True

    def get_message_storage(self):
        return self._extra_data.err_and_warn

    def get_income_data(self):
        """ Возвращает входные данные. """
        return self._income_data

    @property
    def income_data_is_valid(self) -> bool:
        return not self._income_data_errors.errors

    @cached_property
    def rows(self) -> MutableSequence[TableRow]:
        return self._rows

    def get_stages_data(self) -> StagesData | None:
        return self._stages_data

    def get_extra_data(self) -> BaseEntityData:
        return self._extra_data

    @property
    def allow_compare_stages(self):
        return self._extra_data.allow_compare_stages

    def get_max_direction_num(self) -> float:
        return self._stages_data.max_direction

    def get_max_stage(self) -> float:
        return self._stages_data.max_stage


class StageOrDirectionCell:

    common_always_red_pattern = re.compile(r'кр|покоя|крас', re.IGNORECASE)

    __slots__ = (
        '_errors_and_warnings',
        '_sep',
        '_is_always_red',
        '_stages_or_directions_f',
        '_stages_or_directions_string_row',
        '_numbers',
        '_doubles',
        '_bad_nums',
        '_asc_order'
    )

    def __init__(
            self,
            stages_or_directions_string: str,
            sep: str = ',',
            always_red_pattern: str | re.Pattern = ''
    ):

        self._stages_or_directions_string_row = stages_or_directions_string
        self._errors_and_warnings = MessageStorage()
        if isinstance(stages_or_directions_string, str):
            self._stages_or_directions_f = remove_chars(stages_or_directions_string, ' ')
        else:
            raise TypeError(f'{stages_or_directions_string!r} must be a str')
        self._sep = sep
        self._asc_order = False
        self._is_always_red = bool(
            re.findall(self._get_always_red_pattern(always_red_pattern), self._stages_or_directions_f)
        )
        self._process_income_data()

    def __repr__(self):
        attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'{self.__class__.__name__}({attrs})'

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
        nums_as_str = self._stages_or_directions_f.split(self._sep)
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
            self._errors_and_warnings.add_errors(
                Message(f'Недопустимые номера({len(self._bad_nums)}): {"; ".join(n for n in self._bad_nums)}', MessageCategories.validation)
            )
            return
        try:
            assert self._sep.join(str(num) for num in numbers) == self._stages_or_directions_f
        except AssertionError:
            logger.critical(self._create_text_error_in_generation_numbers(numbers))
            raise
        self._numbers = frozenset(unique_nums)
        self._asc_order = self._stages_or_directions_f == ",".join(str(n) for n in sorted(self._numbers))
        if not self._asc_order:
            self._errors_and_warnings.add_warnings(
                Message('Номера не расположены в порядке возрастания', MessageCategories.validation)
            )
        for  num, cnt in self._doubles.items():
            self._errors_and_warnings.add_warnings(
                Message(f'Найдены дубли. Номер={num}, кол-во={cnt}', MessageCategories.validation)
            )

    def _create_text_error_in_generation_numbers(self, numbers: Iterable[int | float]) -> str:
        generated_numbers = 'Сгенерированные номера:'
        income_numbers = 'Входная строка с номерами:'
        indent = max(len(generated_numbers), len(income_numbers))
        return (
            f'Программная ошибка логики: сгенерированные номера не должны различаться со входными:\n'
            f'{generated_numbers:<{indent}} {self._sep.join(str(num) for num in numbers)}\n'
            f'{income_numbers:<{indent}} {self._stages_or_directions_f}\n'
            f'{self}'
        )

    def _get_sep_errors(self) -> Generator[Message, Any, None]:
        if self._stages_or_directions_f[-1] == self._sep:
            yield Message(
                f'Строка не должна заканчиваться разделителем "{self._sep}"', MessageCategories.validation
            )
        more_than_one_sep_char_in_string = re.findall(self._sep + r'{2,}', self._stages_or_directions_f)
        if more_than_one_sep_char_in_string:
            yield Message(
                f'Найдено более одного разделяющего символа "{self._sep}" подряд.', MessageCategories.validation
            )

    def get_stages_or_directions_string_row(self) -> str:
        return self._stages_or_directions_string_row

    def get_errors(self) -> Sequence[Message]:
        return self._errors_and_warnings.errors

    def get_numbers(self) -> Set[int | float]:
        return self._numbers

    def get_numbers_as_str(self, sep='') -> str:
        return stages_as_string(self._numbers, sep or self._sep)

    def get_bad_nums(self) -> Sequence[str]:
        return self._bad_nums

    def get_numbers_as_int_or_float(self) -> Set[str]:
        return self._numbers

    def get_doubles(self) -> MutableMapping[int | float, int]:
        return self._doubles

    @property
    def is_asc_order(self):
        return self._asc_order

    @property
    def value(self):
        return self._stages_or_directions_string_row

    @property
    def is_valid(self):
        return not self._errors_and_warnings.errors and not self._bad_nums

    @property
    def is_always_red(self) -> bool:
        return self._is_always_red


@dataclass(slots=True, frozen=True)
class NumbersDiscrepancy:
    number: stages_or_direction_num
    missing_numbers: Iterable[stages_or_direction_num]

    def get_sorted_missing_numbers(self, key=None):
        return sorted(self.missing_numbers, key=key)


class ComparisonExtraData(NamedTuple):
    num_type: int
    description: str


comparison_directions_and_stages_data = {
    (TableNames.directions_table, ColNamesDirectionsTable.stages, TableNames.time_program, ColNamesTimeProgramsTable.directions):
        ComparisonExtraData(1, ComparisonDescriptions.directions_table_to_time_table),
    (TableNames.directions_table, ColNamesDirectionsTable.stages, TableNames.directions_table, ColNamesDirectionsTable.stages):
        ComparisonExtraData(2, ComparisonDescriptions.two_directions_table),
    (TableNames.time_program, ColNamesTimeProgramsTable.directions, TableNames.time_program, ColNamesTimeProgramsTable.directions):
        ComparisonExtraData(3, ComparisonDescriptions.two_time_program_tables)
    }


class SourceComparisonMeta(NamedTuple):
    table_name: TableNames
    cell_name: ColNamesDirectionsTable | ColNamesTimeProgramsTable
    name: str = None
    number: int = None


def get_comparison_data(src: SourceComparisonMeta, dst: SourceComparisonMeta) -> ComparisonExtraData | Iterable[None]:
    return comparison_directions_and_stages_data.get(
        (src.table_name, src.cell_name, dst.table_name, dst.cell_name), itertools.repeat(None)
    )


class ComparisonMeta(ReprMixin):

    def __init__(self, name, src: SourceComparisonMeta, dst: SourceComparisonMeta):
        self.name = name
        self.src = src
        self.dst = dst
        self.num_type, self.description = get_comparison_data(src, dst)


class AbstractComparison:

    mappings = {k: v for k, v in comparison_directions_and_stages_data.values()}
    allowed_src_dst_pairs: Container

    def __init__(
            self,
            first,
            second,
            meta: ComparisonMeta = None,
            compare_immediately=True
    ):
        self._first = first
        self._second = second
        self._meta = meta or ComparisonMeta(None, None, None)
        self._missing_in_first: MutableSequence[NumbersDiscrepancy] = []
        self._missing_in_second: MutableSequence[NumbersDiscrepancy] = []
        self._comparison_is_done = False
        if compare_immediately:
            self.compare()

    @abstractmethod
    def compare(self):
        raise NotImplementedError()

    def get_first(self):
        return self._first

    def get_second(self):
        return self._second

    def get_missing_in_first(self) -> MutableSequence[NumbersDiscrepancy]:
        return self._missing_in_first

    def get_missing_in_second(self) -> MutableSequence[NumbersDiscrepancy]:
        return self._missing_in_second

    def get_meta(self) -> ComparisonMeta:
        return self._meta

    @property
    def has_discrepancy(self) -> bool:
        return bool(self._missing_in_first or self._missing_in_second)

    def _get_sorted_nums(self, src: MutableSequence[NumbersDiscrepancy]) -> dict[stages_or_direction_num, MutableSequence[stages_or_direction_num]]:
        return {obj.number: obj.get_sorted_missing_numbers() for obj in src}

    def dump(self):
        return {
            str(Fields.comparison_is_done): self._comparison_is_done,
            str(Fields.has_discrepancy): self.has_discrepancy,
            str(Fields.src_num): self._meta.src.number,
            str(Fields.dst_num): self._meta.dst.number,
            str(Fields.missing_in_src): self._get_sorted_nums(self._missing_in_first),
            str(Fields.missing_in_dst): self._get_sorted_nums(self._missing_in_second)
        }


missing_data: TypeAlias = MutableSequence[tuple[stages_or_direction_num, MutableSequence[stages_or_direction_num]]]


class ComparisonDirectionsAndStages(AbstractComparison, ReprMixin):

    allowed_src_dst_pairs = comparison_directions_and_stages_data

    def compare(self):
        allowed_to_compare = all(isinstance(obj, MutableMapping) for obj in (self._first, self._second))
        if not allowed_to_compare:
            raise TypeError(f'Invalid type attrs "self._first" and "self._second"')
        self._missing_in_second, self._missing_in_first = compare(self._first, self._second)
        self._comparison_is_done = True
        # print(f'self._missing_in_first: {self._missing_in_first}')
        # print(f'self._missing_in_second: {self._missing_in_second}')


def compare(
    first: stages_or_direction_container,
    second: stages_or_direction_container
):
    def get_discrepancies(src, dst):
        discrepancies = []
        for k, v in src.items():
            try:
                missing_nums = v - dst[k]
                if missing_nums:
                    discrepancies.append(NumbersDiscrepancy(k, missing_nums))
            except KeyError:
                if v:
                    discrepancies.append(NumbersDiscrepancy(k, v))
        return discrepancies
    return get_discrepancies(first, second), get_discrepancies(second, first)


def compare_stages_data_for_directions_and_time_programs(
    mapping_from_direction_table: StagesData,
    mapping_from_time_programs_table: Iterable[tuple[int, StagesData]]
):
    directions_to_stage_from_direction_table = mapping_from_direction_table.get_direction_to_stages_mapping()
    for num, stage_data in mapping_from_time_programs_table:
        directions_to_stage_from_stages_table = stage_data.get_direction_to_stages_mapping()
        yield ComparisonDirectionsAndStages(
            directions_to_stage_from_direction_table,
            directions_to_stage_from_stages_table,
        )


@dataclass(frozen=True, slots=True)
class DirectionBaseProperties:
    num: int | float | str
    type: DirectionEntities
    stages: str
    errors: list[dict]


if __name__ == '__main__':
    stages = StageOrDirectionCell('1,2,3,,4,3,')
    print(stages)
    stages2 = StageOrDirectionCell('пост. кр')
    print(stages2)
    stages3 = StageOrDirectionCell('1ю3ю4.4,')
    print(stages3)
    stages4 = StageOrDirectionCell('1,2,7e, 8.2 ')
    print(stages4)
    print(stages4.is_valid)








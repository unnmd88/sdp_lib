import inspect
import itertools
import logging
import pprint
import re
from abc import abstractmethod
from collections import deque
from dataclasses import dataclass, field
from functools import cached_property
from itertools import zip_longest
from typing import NamedTuple
from collections.abc import (
    MutableMapping,
    Iterable,
    Sequence,
    Generator,
    Set, MutableSequence, Collection
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
    DirectionTypes,
    RowNames, MessageLevels
)
from sdp_lib.passport.mixins import ReprMixin
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import remove_chars, get_arg_names
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
    level: MessageLevels = MessageLevels.debug


def add_record(
    container: MutableSequence[Message] | MutableMapping[float, Any],
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
    name: ColNamesDirectionsTable | ColNamesTimeProgramsTable | str
    init_val: Any
    default_val: Any
    value: Any
    is_valid: bool = True


def get_number_cell_data(
    init_val: str | int | float,
    name: ColNamesTimeProgramsTable | ColNamesDirectionsTable
) -> Cell:
    default_val, is_valid = None, True
    val = get_int_or_float(init_val)
    if val is None:
        is_valid = False
        val = None
    return Cell(name, init_val, default_val, val, is_valid)


def get_cell_data(
    name: str,
    init_val: Any,
    default_val=None,
    is_valid: bool = True
) -> Cell:
    return Cell(name, init_val, default_val, init_val or default_val, is_valid)


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
        if flag and self._permission_to_set_flag_from_false_to_true is False:
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
            sort: bool = True
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


class AbstractEntity:
    """ Абстрактный класс любой сущности паспорта(Row, Table и т.д.)"""

    name: RowNames | TableNames

    def __init__(self):
        self._data = BaseEntityData(self.name)

    def __repr__(self):
        attrs = ' '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'{self.__class__.__name__}({attrs})'


class AbstractTable(AbstractEntity):
    """ Абстрактный базовый класс таблицы паспорта. """

    allowed_cnt_row_props: set
    row_class: Any

    def __init__(self, income_data: str):
        super().__init__()
        self._income_data = income_data
        self._income_data_errors = MessageStorage(StorageNames.income_data)
        if self.name == TableNames.directions_table:
            self._stages_data = StagesData(StagesMapping.direction_to_stages)
        elif self.name == TableNames.time_program:
            self._stages_data = StagesData(StagesMapping.stage_to_direction)
        else:
            self._stages_data = None
        self._check_raw_data()
        self._rows: MutableMapping[float, Any] = {}
        self._rows_with_errors: MutableMapping[float, Any] = {}
        self._build()

    def _build(self):
        self._data.err_and_warn.clear_all()
        rows = self._income_data.rstrip().split('\n')
        if len(rows) <= 1:
            self._data.err_and_warn.add_errors(Message(Text.income_table_text_rule))
            return
        for i, string_data in enumerate(rows):
            row_properties = remove_chars(string_data, ' ').split()
            if len(row_properties) not in self.allowed_cnt_row_props:
                self._data.err_and_warn.add_errors(Message(Text.income_table_text_rule))
                return
            elif len(row_properties) == 14 and self.name == TableNames.directions_table:
                t_zz = 0
                row_properties = [p if i != 10 else t_zz for i, p in enumerate(row_properties)]
            elif len(row_properties) == 1:
                if self.name == TableNames.directions_table:
                    num, direction_type, stages = str(i + 1), DirectionTypes.common, row_properties[0]
                    row_properties = [num, direction_type, stages]
            elif len(row_properties) == 2 and self.name == TableNames.time_program:
                num_pp, num_stage, directions,  = i + 1, row_properties[0], row_properties[1]
                row_properties = [num_pp, num_stage, directions]
            instance = self.row_class(i, *row_properties)
            if instance.number.is_valid:
                key = instance.number.value
                self._load_row((key, instance))
            else:
                key = instance.number.init_val
                self._load_row_with_err((key, instance))
        self._set_permission_for_compare_stages()
        self._load_data_to_stages_data()

    def _check_raw_data(self) -> bool:
        """
        Проверяет валидность атрибута self._income_data
        :return: True если входные данные валидны для обработки, иначе False.
        """
        if len(self._income_data) < 4:
            self._income_data_errors.add_errors(
                Message(f'Некорректные данные для обработки и формирования таблицы {self.name}')
            )
        return self.income_data_is_valid

    def _load_row(self, *args: tuple[float, Any]) -> int:
        """
         Добавляет пару ключ-значение в атрибут self._rows.
        :param args: Каждый элемент args - кортеж из 2 элементов, у которого 0 элемент - ключ, а 1 - значение.
        :return: Количество добавленных пар в self._rows
        """
        return add_record(self._rows, args)

    def _load_row_with_err(self, *args: tuple[float, Any]):
        """
         Добавляет пару ключ-значение в атрибут self._rows_with_errors.
        :param args: Каждый элемент args - кортеж из 2 элементов, у которого 0 элемент - ключ, а 1 - значение.
        :return: Количество добавленных пар в self._rows_with_errors
        """
        return add_record(self._rows_with_errors, args)

    def _load_data_to_stages_data(self):
        if self._data.allow_compare_stages:
            if self.name == TableNames.directions_table:
                self._stages_data.build({d.number.value: d.stages.get_numbers() for d in self._rows.values()})
            elif self.name == TableNames.time_program:
                self._stages_data.build({d.number.value: d.directions.get_numbers() for d in self._rows.values()})

    def _set_permission_for_compare_stages(self):
        if self._stages_data is None or any(instance.allow_compare_stages is False for instance in self._rows.values()):
            self._data.permissions.set_val_for_compare_stages(False)

    def get_message_storage(self):
        return self._data.err_and_warn

    def get_income_data(self):
        """ Возвращает входные данные. """
        return self._income_data

    @property
    def income_data_is_valid(self) -> bool:
        return not self._income_data_errors.errors

    def get_rows_with_errors(self) -> MutableMapping[float, Any]:
        return self._rows_with_errors

    def get_all_rows(self) -> MutableMapping[float, Any]:
        return self._rows

    def get_stages_data(self) -> StagesData | None:
        return self._stages_data


class StageOrDirectionCell:

    common_always_red_pattern = re.compile(r'кр|покоя|крас', re.IGNORECASE)

    __slots__ = (
        '_errors_and_warnings',
        '_sep',
        '_is_always_red',
        '_stages_or_directions',
        '_numbers',
        '_doubles',
        '_bad_nums'
    )

    def __init__(
            self,
            stages_or_directions_string: str,
            sep: str = ',',
            always_red_pattern: str | re.Pattern = ''
    ):
        self._errors_and_warnings = MessageStorage()
        if isinstance(stages_or_directions_string, str):
            self._stages_or_directions = remove_chars(stages_or_directions_string, ' ')
        else:
            raise TypeError(f'{stages_or_directions_string!r} must be a str')
        self._sep = sep
        self._is_always_red = bool(
            re.findall(self._get_always_red_pattern(always_red_pattern), self._stages_or_directions)
        )
        self._process_income_data()
        # logger.info(self)

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
            self._errors_and_warnings.add_errors(
                Message(f'Недопустимые номера({len(self._bad_nums)}): {"; ".join(n for n in self._bad_nums)}')
            )
            return
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

    def get_errors(self) -> Sequence[Message]:
        return self._errors_and_warnings.errors

    def get_numbers(self) -> Set[int | float]:
        return self._numbers

    def get_bad_nums(self) -> Sequence[str]:
        return self._bad_nums

    def get_numbers_as_int_or_float(self) -> Set[str]:
        return self._numbers

    def get_doubles(self) -> MutableMapping[int | float, int]:
        return self._doubles

    @property
    def is_valid(self):
        return not self._errors_and_warnings.errors and not self._bad_nums

    @property
    def is_always_red(self) -> bool:
        return self._is_always_red


def compare(
    first: stages_or_direction_container,
    second: stages_or_direction_container
):
    result_has_not_in_second = {}
    result_has_not_in_first = {}
    for k in first:
        has_not_in_second = first[k] - second[k]
        has_not_in_first = second[k] - first[k]
        if has_not_in_first:
            result_has_not_in_first[k] = has_not_in_first
        if has_not_in_second:
            result_has_not_in_second[k] = has_not_in_second
    return result_has_not_in_second, result_has_not_in_first


def compare2(
    first: stages_or_direction_container,
    second: stages_or_direction_container
):
    copy_first = {k: v for k, v in first.items()}
    copy_second = {k: v for k, v in second.items()}
    result_has_not_in_first, result_has_not_in_second = [], []
    stack1 = deque(copy_first.keys())# Направления из Таблицы направлений
    while stack1:
        k1 = stack1.popleft()
        v1 = copy_first.pop(k1) #v1 default = frozenset[int | float]
        try:
            v2 = copy_second.pop(k1) #v2 default = frozenset[int | float]
            has_not_in_second = v1 - v2
            if has_not_in_second:
                result_has_not_in_second.append((k1, sorted(has_not_in_second)))
                # result_has_not_in_second[k1] = sorted(has_not_in_second)
        except KeyError:
            # result_has_not_in_second[k1] = sorted(v1)
            result_has_not_in_second.append((k1, sorted(v1)))
    stack2 = deque(copy_second)
    while stack2:
        k2 = stack2.popleft()
        v2 = copy_second.pop(k2)
        # result_has_not_in_first[k2] = sorted(v2)
        result_has_not_in_first.append((k2, sorted(v2)))
    print(f'result_has_not_in_second: {result_has_not_in_second}')
    print(f'result_has_not_in_first: {result_has_not_in_first}')
    return result_has_not_in_second, result_has_not_in_first


@dataclass(slots=True, frozen=True)
class ResultCompare:
    direction: stages_or_direction_num
    missing_stages: Iterable[stages_or_direction_num]


class AbstractComparison:
    def __init__(self, first, second, name=None, compare_immediately=True):
        self._first = first
        self._second = second
        self._name = name
        self._result_message: Message | None = None
        if compare_immediately:
            self.compare()

    @abstractmethod
    def compare(self):
        raise NotImplementedError()

    @abstractmethod
    def create_message(self):
        raise NotImplementedError()

    def get_first(self):
        return self._first

    def get_second(self):
        return self._second

    def get_name(self):
        return self._name

    def get_result_message(self) -> Message | None:
        return self._result_message


missing_data: TypeAlias = MutableSequence[tuple[stages_or_direction_num, MutableSequence[stages_or_direction_num]]]


class ComparisonStages(AbstractComparison, ReprMixin):

    def __init__(
            self,
            mapping_from_direction_table: stages_or_direction_container,
            mapping_from_time_programs_table: stages_or_direction_container,
            num_time_program: int | None = None,
            compare_immediately: bool = True
    ):
        self._missing_directions_in_table_stages: ResultCompare
        self._missing_directions_in_table_directions: ResultCompare
        super().__init__(
            mapping_from_direction_table,
            mapping_from_time_programs_table,
            num_time_program,
            compare_immediately
        )

    def compare(self):
        allowed_to_compare = all(isinstance(obj, MutableMapping) for obj in (self._first, self._second))
        if not allowed_to_compare:
            raise TypeError(f'Invalid type attrs "self._first" and "self._second"')
        if allowed_to_compare:
            self._missing_directions_in_table_stages, self._missing_directions_in_table_directions = compare3(self._first, self._second)
        print(f'self._missing_directions_in_table_stages: {self._missing_directions_in_table_stages}')
        print(f'self._missing_directions_in_table_directions: {self._missing_directions_in_table_directions}')

    def _get_missing_direction_string(self, pp, num_direction, stages):
        pretty_stages = ','.join(
            str(num) if num not in stages else f'->{num}<-' for num in sorted(self._first[num_direction])
        )
        return f'{pp}) Направление={num_direction}, фазы: {pretty_stages}'

    def create_message(self):
        # if self._missing_directions_in_table_stages:
        missing_directions_in_table_stages = "\n".join(
            self._get_missing_direction_string(i, result_compare.direction, result_compare.missing_stages)
            for i, result_compare in enumerate(self._missing_directions_in_table_stages, 1)
        )
        if missing_directions_in_table_stages:
            missing_directions_in_table_stages = (
            f'Направления, которые присутствуют в фазах в столбце '
            f'"{str(ColNamesDirectionsTable.stages)}"({str(TableNames.directions_table)}), '
            f'но отсутствуют в таблице фаз(Программа {self._name}):\n'
            f'{missing_directions_in_table_stages}'
        )
        self._result_message = Message(missing_directions_in_table_stages)
        return self._result_message


    def get_missing_directions_in_table_stages(self):
        return self._missing_directions_in_table_stages

    def get_missing_directions_in_table_directions(self):
        return self._missing_directions_in_table_stages


def compare3(
    first: stages_or_direction_container,
    second: stages_or_direction_container
):
    copy_first = {k: v for k, v in first.items()}
    copy_second = {k: v for k, v in second.items()}
    result_has_not_in_first, result_has_not_in_second = [], []
    stack1 = deque(copy_first.keys())# Направления из Таблицы направлений
    while stack1:
        k1 = stack1.popleft()
        v1 = copy_first.pop(k1) #v1 default = frozenset[int | float]
        try:
            v2 = copy_second.pop(k1) #v2 default = frozenset[int | float]
            has_not_in_second = v1 - v2
            if has_not_in_second:
                result_has_not_in_second.append(ResultCompare(k1, has_not_in_second))
        except KeyError:
            if v1:
                result_has_not_in_second.append(ResultCompare(k1, v1))
    stack2 = deque(copy_second)
    while stack2:
        k2 = stack2.popleft()
        v2 = copy_second.pop(k2)
        result_has_not_in_first.append(ResultCompare(k2, v2))
    print(f'result_has_not_in_second: {result_has_not_in_second}')
    print(f'result_has_not_in_first: {result_has_not_in_first}')
    return result_has_not_in_second, result_has_not_in_first


def compare_stages_data_for_directions_and_time_programs(
    mapping_from_direction_table: StagesData,
    mapping_from_time_programs_table: Iterable[tuple[int, StagesData]]
):
    directions_to_stage_from_direction_table = mapping_from_direction_table.get_direction_to_stages_mapping()
    for num, stage_data in mapping_from_time_programs_table:
        directions_to_stage_from_stages_table = stage_data.get_direction_to_stages_mapping()
        yield ComparisonStages(
            directions_to_stage_from_direction_table,
            directions_to_stage_from_stages_table,
            num
        )



# def compare_stages_data_for_directions_and_time_programs(
#     mapping_from_direction_table: StagesData,
#     mapping_from_time_programs_table: Iterable[tuple[int, StagesData]]
# ):
#     directions_to_stage_from_direction_table = mapping_from_direction_table.get_direction_to_stages_mapping()
#     for num, stage_data in mapping_from_time_programs_table:
#         directions_to_stage_from_stages_table = stage_data.get_direction_to_stages_mapping()
#         missing_in_table_stages, missing_in_table_directions = compare2(first=directions_to_stage_from_direction_table, second=directions_to_stage_from_stages_table)
#         print(f'missing_in_table_stages: {missing_in_table_stages}')
#         print(f'missing_in_table_directions: {missing_in_table_directions}')
#         yield missing_in_table_stages, missing_in_table_directions






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

    d1 = {
        1: frozenset([1, 2, 3]),
        2: frozenset([3, 4, 5]),
        3: frozenset([6, 7, 8]),

    }

    d2 = {
        1: frozenset([1, 2, 3]),
        2: frozenset([3, 4, 5]),
        3: frozenset([6, 7, 8, 9]),
    }
    print(d1.keys() == d2.keys())
    compare(d1, d2)





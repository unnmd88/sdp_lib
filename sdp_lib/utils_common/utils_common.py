import functools
import inspect
import ipaddress
import itertools
import json
import random
import re
import time
from collections.abc import Sequence, MutableMapping, Iterable, MutableSequence, Hashable, Container, Generator, \
    MappingView
from datetime import datetime as dt
from enum import Enum
from string import ascii_letters
from typing import Callable, TypeVar, Any, Protocol

from sdp_lib.num_stage_or_direction import StageOrDirectionNumber

T = TypeVar('T')

def timed(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        print(f'func: {func.__name__}')
        res = func(*args, **kwargs)
        print(f'Время работы: {time.perf_counter() - start_time}')
        return res
    return wrapper


def get_curr_datetime(sep: str = ':') -> str:
    """
    Возвращает текущую дату и время
    :param sep: разделитель между датой и временем
    :return: отформатированная строка с датой и временем
    """

    return dt.today().strftime(f"%Y-%m-%d %H{sep}%M{sep}%S")


def reverse_slashes(path: str) -> str:
    """
    Разворачивает слеши c "\" или "\\" на "/" пути path
    :param path: строка с путём, в которой необходимо развернуть слеши
    :return: строка - path с развёрнутыми слешами
    """

    return path.replace('\\', '/')


def write_data_to_file(data_for_write: list[str] | str, filename: str, mode: str = 'w') -> None:
    """
    Записывает данные в файл.
    :param data_for_write: Данные, которые будут записаны в файл
    :param filename: Имя файла
    :param mode: Режим записи
    :return: None
    """

    with open(filename, mode) as f:
        if isinstance(data_for_write, str):
            f.write(data_for_write)
        elif isinstance(data_for_write, list):
            for line in data_for_write:
                f.write(f'{line}\n')
        else:
            raise TypeError('Данные для записи в файл должны быть строкой или списком')


def check_is_ipv4(ip_v4: str) -> bool:
    """
    Проверят валидность ip_v4.
    :param ip_v4: Строка с ip адресом, которая будет проверена на валидность.
                  Пример: 192.168.0.1
    :return: True если ip_v4 валидный, иначе False.
    """
    try:
        ipaddress.IPv4Address(ip_v4)
        return True
    except ipaddress.AddressValueError:
        return False


def get_random_word(chars: int = 6):
    return "".join([random.choice(ascii_letters) for _ in range(chars)])


def remove_duplicates(elements: Sequence[T]) -> list[T]:
    """
    Удаляёт дубликаты элементов последовательности с сохранением порядка.
    :param elements: Последовательность элементов, в которой необходимо удалить дубли.
    :return: Список уникальных элементов из elements.
    """
    return list({e: None for e in elements})


def convert_value_to_string(value: Any) -> str:
    """
    Конвертирует экземпляр в строковый тип.
    :param value: Значение, которое будет сконвертировано в строковый тип.
    :return: Строковое представление value.
    """
    return str(value)


def format_time(timestamp) -> str:
    try:
        return timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        return timestamp


def remove_chars(string, *args: str) -> str:
    if not isinstance(string, str):
        raise TypeError('arg "string" must be a str')
    if args == (' ', ):
        return  string.replace(' ', '')

    pattern = spaces = ''
    for char in args:
        if char == ' ':
            spaces = '\s+'
        else:
            pattern += char
    return re.sub('[' + pattern + spaces + ']', '', string)


def read_file_as_string(filepath, rstrip=True, lstrip=True) -> str:
    with open(filepath, encoding='utf-8') as f:
        string = ''.join(line for line in f)
        if rstrip and lstrip:
            string = string.lstrip().rstrip()
        elif rstrip:
            string = string.rstrip()
        elif lstrip:
            string = string.lstrip()
        return string


def get_arg_names(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f'args: {inspect.signature(func)}')
        print(f'args: {inspect.getfullargspec(func).args}')
        return func(*args, **kwargs)
    return wrapper


def stages_as_string(stages: Iterable[str | int | float], sep=',') -> str:
    return sep.join(str(n) for n in sorted(stages))


def sorting_storage(storage: Iterable):
    return sorted(storage)


def to_json(data: dict, file: str = None):
    data = json.dumps(data, ensure_ascii=False, indent=4)
    if isinstance(file, str):
        file =  file if file.endswith('.json') else f'{file}.json'
        with open(file, 'w', encoding='utf-8') as f:
            f.write(data)
    return data


def get_max_or_default_if_target_is_empty(target: Iterable, returned_default_val=None):
    print(f'target: {target}')
    return max(target, default=returned_default_val)


def check_stage_or_direction_num_is_allowed_integer(val: str) -> bool:
    """
    Проверяет, является ли val допустимым номером фазы/направления, представленным целым числом.
    Валидные значения: int(val) > 0.
    :param val: Проверяемое значение.
    :return: True, если является, иначе False.
    """
    return bool(val.isdigit() and val != '0')


def check_stage_or_direction_num_is_allowed_float(val: str) -> bool:
    """
    Проверяет, является ли val допустимым номером фазы/направления, представленным числом с точкой.
    Валидные значения: целая часть(до ".") представлена int > 0, а дробная часть(после ".") представлена
    цифрой от 0-9.
    :param val: Проверяемое значение.
    :return: True, если является, иначе False.
    """
    assumption_is_float = val.split('.')
    if len(assumption_is_float) != 2:
        return False
    before_dot, after_dot = assumption_is_float
    return bool(
        check_stage_or_direction_num_is_allowed_integer(before_dot) and len(after_dot) == 1 and after_dot.isdigit()
    )


def get_stage_or_direction_number_or_none(val: str) -> int | float | None:
    """
    Проверяет, является ли значение val допустимым номером фазы/направления.
    Допустимые номера:
        1. Натуральное число.
        2. Число с точкой, где целая часть(до ".") представлена натуральным числом,
           а дробная часть(после ".") представлена цифрой от 0-9.
    Примеры допустимых номеров: "1", "4", "26", "1.2", "5.1", "32.4" и т.д.
    :param val: Проверяемое значение номера направления/фазы.
    :return: int, если номер соответствует п.1, float, если если номер соответствует п.2, иначе None.

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
    val_s = str(val)
    if check_stage_or_direction_num_is_allowed_integer(val_s):
        return int(val_s)
    if check_stage_or_direction_num_is_allowed_float(val_s):
        return float(val_s)
    return None


# def get_stage_or_direction_number(
#     val: str
# ) -> int | float:
#     """
#     Основная функция, содержащая логику определения валидности номера фазы или направления.
#     На вход подается строка с номером, который вернёт int или float, если номер валидный,
#     иначе вернёт None.
#     Допустимыми считаются следующие типы номеров: целые числа или числа через точку,
#     где после точки стоит единственная цифра от 1 до 9.
#     Примеры допустимых номеров: "1", "4", "26", "1.2", "5.1", "32.4" и т.д.
#     Превращает объект val в тип int | float | None.
#     :param val: Объект строки из которого будет получен объект int | float | None.
#     :return: Если строка val является целым числом, возвращает int(val).
#              Если строка val является числом с точкой, у которого после точки стоит
#              одна единственная целая цифра от 1 до 9, функция вернёт float(val).
#              Иначе возвращает None.
#
#     Примеры
#     --------
#     # >>> get_int_or_float("1")
#     # 1
#     # >>> get_int_or_float("2.1")
#     # 2.1
#     # >>> get_int_or_float("3.2")
#     # 3.2
#     # >>> get_int_or_float("4.45")
#     # None
#     # >>> get_int_or_float("abracadabra")
#     None
#
#     """
#     if not isinstance(val, (str, int, float)):
#         raise TypeError(
#             f'get_stage_or_direction_number() argument must be a string, int or float, not "{type(val).__name__!r}"'
#         )
#     val = str(val)
#     if val.isdigit():
#         return int(val)
#     else:
#         assumption_is_float = val.split('.')
#         if len(assumption_is_float) != 2:
#             raise ValueError(f'invalid literal: {val!r}.')
#         before_dot, after_dot = assumption_is_float
#         if len(after_dot) != 1 or not after_dot.isdigit() or not before_dot.isdigit():
#             raise ValueError(f'invalid literal after dot: {val!r}.')
#         return StageOrDirectionNumber(float(val))


def remove_left_light_spaces(sequence: Iterable[str]):
    return (s.rstrip().lstrip() for s in sequence)


def add_record(
    target: MutableSequence | MutableMapping,
    records: Iterable[Any] | Iterable[tuple[Hashable, Any]],
    skip_add_if_err_is_empty=True
) -> int:
    cnt = 0
    if isinstance(target, MutableMapping):
        for k, v in records:
            if str(v) or not skip_add_if_err_is_empty:
                cnt += 1
                target[k] = v
    elif isinstance(target, MutableSequence):
        for record in records:
            if str(record) or not skip_add_if_err_is_empty:
                cnt += 1
                target.append(record)
    return cnt


class DumpProtocol(Protocol):
    __slots__: tuple[str, ...]
    __dict__: dict[str, Any]


def dump_to_dict(obj: DumpProtocol):
    try:
        return {attr: getattr(obj, attr) for attr in obj.__slots__}
    except AttributeError:
        return {k: v for k, v in obj.__dict__.items()}


def dump_to_tuple(obj: DumpProtocol):
    try:
        return ((attr, getattr(obj, attr)) for attr in obj.__slots__)
    except AttributeError:
        return (pair for pair in obj.__dict__.items())


def gen_seq(
    pattern: Sequence,
    exclude_positions: Container[int] = None,
    exclude_values: Container[Any] = None,
    returned_container = tuple,
):
    exclude_positions = exclude_positions or ()
    exclude_values = exclude_values or ()
    return returned_container(
        el for i, el in enumerate(pattern) if (i not in exclude_positions) and (el not in exclude_values)
    )


def get_instance_properties(instance) -> Generator[MappingView, Any, None]:
    """
    Возвращает итератор по всем @properties в виде ключ-значение.
    :param instance: Любой объект.
    :return: Возвращает итератор по всем @properties в виде ключ-значение.
    """
    _all_classes = itertools.chain(
        *(c.__dict__.items() for c in instance.__class__.__bases__ if c != object),
        instance.__class__.__dict__.items()
    )
    return (k for k, v in _all_classes if not k.startswith('__') and isinstance(v, property))


def create_repr_from_dict_xor_slots(
    instance,
    include_properties: bool = True,
    exclude_startswith: str = '__',
    splitter: str = ' '
):
    """
    Возвращает строковое представление объекта.
    :param instance: Любой объект.
    :param include_properties: Если True - добавляет @properties.
    :param exclude_startswith: Исключает атрибуты, начинающиеся с exclude_startswith.
    :param splitter: Разделитель между атрибутами.
    :return: Строковое представление объекта. Например:
             MyClass(attr1=1 attr2=True, attr3=[1, 2, 3, 4])
    """
    if hasattr(instance, '__dict__') and hasattr(instance, '__slots__'):
        raise ValueError(f'An instance should not have "__dict__" and "__slots__" at the same time.')
    try:
        src = instance.__dict__.keys()
    except AttributeError:
        src = instance.__slots__
    p = (get_instance_properties(instance)) if include_properties else ()
    attrs = splitter.join(
        f'{attr}={getattr(instance, attr)!r}'
        for attr in itertools.chain(src, p) if not attr.startswith(exclude_startswith)
    )
    return f'{instance.__class__.__name__}({attrs})'


def get_vector_from_enum(src: Enum, startswith: str, exclude_names: Container = ()):
    for name in src:
        if name.name.startswith(startswith) and name.value not in exclude_names:
            yield name.value


if __name__ == '__main__':


    print(remove_chars('пн   ,  вт ,с  р ,ч т  ,   пт:', ':', ' '))
    print(get_max_or_default_if_target_is_empty([]))
    """
    Программа 1 Тц = 353 с. пн,вт,ср,чт,пт: 

07:00:00-09:00:00 
17:00:00-19:00:00 
    """

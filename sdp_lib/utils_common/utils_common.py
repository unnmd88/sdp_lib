import functools
import inspect
import ipaddress
import json
import random
import re
import time
from collections.abc import Sequence, MutableMapping, Iterable, MutableSequence, Hashable
from datetime import datetime as dt
from string import ascii_letters
from typing import Callable, TypeVar, Any, Protocol

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


if __name__ == '__main__':


    print(remove_chars('пн   ,  вт ,с  р ,ч т  ,   пт:', ':', ' '))
    print(get_max_or_default_if_target_is_empty([]))
    """
    Программа 1 Тц = 353 с. пн,вт,ср,чт,пт: 

07:00:00-09:00:00 
17:00:00-19:00:00 
    """

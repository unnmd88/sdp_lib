from collections.abc import Iterable, Sequence
from enum import StrEnum
from typing import Any

from sdp_lib.passport.constants import ColNamesTimeProgramsTable, ColNamesDirectionsTable, DirectionEntities, TableNames


class Text(StrEnum):
    bad_num_pp = (
        f'Не задан "{str(ColNamesTimeProgramsTable.num_pp)}" для фазы. '
        f'Допускаются номера в виде целых чисел("1", "2", "6" и т.д) или '
        f'числа через точку("1.1", "1.2", "4.1" и т.д.)'
    )
    typo_in_name = 'Опечатка в названии'
    name_error = 'Ошибка в названии'
    cell_is_empty = 'Ячейка пуста '
    invalid_name = 'Недопустимое название'
    is_not_a_number = 'Значение не является числом'
    has_not_num_tlc = 'Нет номеров светофоров'
    invalid_type_tlc = 'Неверный тип светофора'
    invalid_value = 'Недопустимое значение'
    invalid_value_for_direction_entity = 'Недопустимое значение для данного типа направления'

    always_red_must_be_empty = (
        f'У группы типа "{DirectionEntities.always_red}" не должно быть фаз в '
        f'колонке "{ColNamesDirectionsTable.stages}"'
    )

    bad_number = 'Неверный номер'

    income_table_text_rule = (
        f'Некорректные входные данные для обработки. Каждая строка таблицы'
        f'должна начинаться с новой строки("/n"), а каждое значение в'
        f'строке должно быть разделено пробелом или табуляцией.'
    )

    @classmethod
    def expected_col_name(cls, expected_name: str):
        return f'Данная колонка должна иметь название: {expected_name}.'

    @classmethod
    def bad_cols_num(cls, num: int, expected: Any):
        return f'Недопустимое количество колонок: {num}. Допустимо: {expected}'

    @classmethod
    def bad_min_rows_num(cls, num: int, expected_gt: int):
        return f'Минимальное количество строк должно быть больше: {expected_gt}. В таблице: {num}'

    @classmethod
    def misspell(cls, expected: str):
        return f'Опечатка в названии. Используйте: <{expected}>'

    @classmethod
    def invalid_nums(cls, nums: Iterable):
        return f'Некорректные номера: {", ".join(str(n) for n in nums)}'

    @classmethod
    def doubles(cls, doubles: Iterable[tuple[Any, int]]):
        _doubles = ", ".join(f'{str(el)}: {str(cnt)}' for el, cnt in doubles)
        return f'Найдены дубли: {_doubles}'

    @classmethod
    def illegal_pos_for_char(cls, char):
        return f'Ошибка "{char}" в строке'

    @classmethod
    def several_char_together(cls, char):
        return f'Несколько {char} подряд'

    @classmethod
    def bad_value(cls, val, expected=''):
        if expected:
            return f'Недопустимое значение <{val}>. Допустимые: {expected}'
        return f'Недопустимое значение.'

    @classmethod
    def invalid_col_names(cls, entity, names):
        return f'Некорректные имена столбцов для {entity}: {names}'

    @classmethod
    def bad_length(cls, val, expected=''):
        return f'Недопустимое количество колонок <{val}>. Допустимое количество: {expected}'

    @classmethod
    def bad_num_rows(cls, val, expected=''):
        return f'Недопустимое количество строк <{val}>. Допустимое количество больше {expected}'

    @classmethod
    def get_bad_num(
            cls,
            num_stage: str | int = '',
            cell_name: ColNamesTimeProgramsTable | ColNamesDirectionsTable = ''
    ) -> str:
        return  f'Неверно задан номер в ячейке "{str(cell_name)}": {num_stage}'

    @classmethod
    def val_must_be_gt(cls, gt_val):
        return f'Значение не должно быть меньше {gt_val}'

    @classmethod
    def val_must_be_lt(cls, lt_val):
        return f'Значение не должно быть больше {lt_val}'

    @classmethod
    def direction_entity_not_defined(cls):
        return f'Тип направления не задан'



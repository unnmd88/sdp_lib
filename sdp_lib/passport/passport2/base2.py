from collections.abc import MutableSequence, Sequence
from functools import cached_property
from typing import NamedTuple, Any

from sdp_lib.passport.constants import MessageCategories
from sdp_lib.utils_common.utils_common import add_record, create_repr_from_dict_xor_slots


class StageOrDirectionNumber:

    __slots__ = ('_value', )

    def __init__(self, value: int | float):
        self._value = value

    @cached_property
    def value(self):
        return self._value


def get_stage_or_direction_number(
    val: str
) -> StageOrDirectionNumber | None:
    """
    Основная функция, содержащая логику определения валидности номера фазы или направления.
    На вход подается строка с номером, который вернёт int или float, если номер валидный,
    иначе вернёт None.
    Допустимыми считаются следующие типы номеров: целые числа или числа через точку,
    где после точки стоит единственная цифра от 1 до 9.
    Примеры допустимых номеров: "1", "4", "26", "1.2", "5.1", "32.4" и т.д.
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
    None

    """
    if isinstance(val, StageOrDirectionNumber):
        return val
    if not isinstance(val, (str, int, float)):
        raise TypeError(
            f'get_stage_or_direction_number() argument must be a string, int or float number, not "{type(val).__name__!r}"'
        )
    val = str(val)
    if val.isdigit():
        return StageOrDirectionNumber(int(val))
    else:
        assumption_is_float = val.split('.')
        if len(assumption_is_float) != 2:
            raise ValueError(f'invalid literal: {val!r}.')
        before_dot, after_dot = assumption_is_float
        if len(after_dot) != 1 or not after_dot.isdigit() or not before_dot.isdigit():
            raise ValueError(f'invalid literal after dot: {val!r}.')
        return StageOrDirectionNumber(float(val))


class Message(NamedTuple):
    text: str
    category: MessageCategories | int


class MessageStorage(NamedTuple):

    errors: MutableSequence[str | Message]
    warnings: MutableSequence[str | Message]

    def add_errors(self, *errors: Message):
        return add_record(self.errors, errors)

    def add_warnings(self, *warnings: Message):
        return add_record(self.warnings, warnings)

    def clear_all(self):
        self.errors.clear()
        self.warnings.clear()

    # def get_errors_by_categories(self, message_as_text=True):
    #     res = {}
    #     for msg in self.errors:
    #         m = msg.text if message_as_text else msg
    #         try:
    #             res[int(msg.category)][Fields.messages].append(m)
    #         except KeyError:
    #             cat, description = categories_descriptions.get(int(msg.category), (None, None))
    #             res[cat] = {
    #                 str(Fields.category_description): description,
    #                 str(Fields.messages): [m]
    #             }
    #     return res


class ValidationData(NamedTuple):
    value: Any
    is_valid: bool


class CellData:

    __slots__ = ('value', 'text', 'context', 'doubles')

    def __init__(
            self,
            value: str = None,
            text_is_valid: bool = None,
            context_is_valid: bool = None,
            doubles: Sequence = None,
    ):
        self.value = value
        self.text = text_is_valid
        self.context = context_is_valid
        self.doubles = doubles

    def __repr__(self):
        return create_repr_from_dict_xor_slots(self)


class AbstractRow:
    def __init__(self, row: Sequence[CellData] | MutableSequence[CellData]):
        self._row = row


class DirectionRow(AbstractRow):
    pass


if __name__ == '__main__':
    inst = CellData()
    print(inst)
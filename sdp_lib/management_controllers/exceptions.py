from typing import Any


class BadIpv4(Exception):

    def __str__(self):
        return f'Некорректный ip-v4 адрес'


class BadControllerType(Exception):
    message = 'Некорректный тип контроллера'

    def __init__(self, type_controller=None):
        self.type_controller = type_controller
    def __str__(self):
        return self.message if self.type_controller is None else f'{self.message}: {self.type_controller}'


class ConnectionTimeout(Exception):

    def __str__(self):
        return f'Превышено время подключения'


class ErrorSetValue(Exception):
    message = 'Ошибка отправки команды'

    def __init__(self, type_controller=None):
        self.type_controller = type_controller

    def __str__(self):
        return self.message if self.type_controller is None else f'{self.message}: {self.type_controller}'


class BadValueToSet(ValueError):

    pattern_invalid_value = 'Невалидное значение'

    def __init__(
            self,
            value: str | int,
            expected: str | set[Any] | tuple[str | int, str | int]
    ):
        self.given_value = value
        self.expected = self._make_expected_text(expected)

    def __str__(self):
        return f'{self.pattern_invalid_value} <{self.given_value}>. {self.expected}'.rstrip()

    def _make_expected_text(self, expected):
        if isinstance(expected, str):
            return f'Должно равняться {expected}'
        elif isinstance(expected, set):
            return f'Должно быть одним из значений: {expected}'
        elif isinstance(expected, tuple) and len(expected) == 2:
            return f'Должно быть в диапазоне от {str(expected[0])} до {str(expected[1])}'
        else:
            return ''


class ReadFromInteractiveShellError(TimeoutError):

    message = 'Ошибка сеанса интерактивной оболочки'

    def __str__(self):
        return self.message




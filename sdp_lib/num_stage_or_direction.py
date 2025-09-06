from functools import cached_property


class StageOrDirectionNumber:

    __slots__ = ('_value', )


    def __init__(self, value: int | float):
        self._value = value

    @cached_property
    def value(self):
        return self._value

    def _build(self):
        pass
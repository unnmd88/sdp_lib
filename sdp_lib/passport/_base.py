from collections.abc import (
    MutableSequence
)

from sdp_lib.passport.utils import add_record


class AbstractEntity:
    def __init__(self):
        self._errors = []
        self._warnings = []

    def __repr__(self):
        attrs = ' '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'{self.__class__.__name__}({attrs})'

    def add_errors(self, *errors: str):
        return add_record(self._errors, errors)

    def add_warnings(self, *warnings: str):
        return add_record(self._errors, warnings)

    def get_errors(self) -> MutableSequence[str]:
        return self._errors

    def get_warnings(self) -> MutableSequence[str]:
        return self._warnings

    @property
    def is_valid(self) -> bool:
        return not bool(self._errors)


if __name__ == '__main__':
    o = AbstractEntity()
    print(o)

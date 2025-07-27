from dataclasses import (
    dataclass,
    field
)
from typing import (
    Any,
    NamedTuple, TypeAlias
)
from collections.abc import (
    MutableSequence,
    Iterable,
    MutableMapping
)

from sdp_lib.passport.constants import (
    MessageLevels,
    StorageNames, StagesMapping
)


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


stages_content_type: TypeAlias = MutableMapping[float, set[float]]


@dataclass
class StagesData:
    mapping_type: StagesMapping
    _direction_to_stages_mapping: stages_content_type = field(default_factory=dict)
    _stage_to_direction_mapping: stages_content_type = field(default_factory=dict)

    def refresh(self, data: dict[float, set]):
        if self.mapping_type == StagesMapping.direction_to_stages:
            self._direction_to_stages_mapping = {k: v for k, v in data.items()}
            self._stage_to_direction_mapping.clear()
            for direction, stages in self._direction_to_stages_mapping.items():
                for stage in stages:
                    try:
                        self._stage_to_direction_mapping[stage].add(direction)
                    except KeyError:
                        self._stage_to_direction_mapping[stage] = {direction}
        elif self.mapping_type == StagesMapping.stage_to_direction:
            self._stage_to_direction_mapping = {k: v for k, v in data.items()}

    def get_direction_to_stages_mapping(self):
        return self._direction_to_stages_mapping

    def get_stage_to_direction_mapping(self):
        return self._stage_to_direction_mapping


@dataclass
class StagesData2:
    pass




# @dataclass(slots=True)
class Actions:

    __slots__ = ('_compare_stages', '_allow_from_false_to_true')

    def __init__(
            self,
            *,
            compare_stages: bool = True
    ):
        self._compare_stages = compare_stages
        self._allow_from_false_to_true: bool = False

    def __repr__(self):
        attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'{self.__class__.__name__}({attrs})'

    def set_permission_set_flag_from_false_to_true(self, value: bool):
        self._allow_from_false_to_true = bool(value)

    def _check_permission_and_return_flag(self, flag: bool):
        flag = bool(flag)
        if flag and self._allow_from_false_to_true is False:
            raise AttributeError("can't set attribute from False to True")
        return flag

    def set_compare_stages(self, flag: bool):
        self._compare_stages = self._check_permission_and_return_flag(flag)

    @property
    def compare_stages(self) -> bool:
        return self._compare_stages


if __name__ == '__main__':
    act = Actions()
    print(act)
    act.set_compare_stages(False)
    act.set_permission_set_flag_from_false_to_true(True)
    act.set_compare_stages(True)
    print(act)

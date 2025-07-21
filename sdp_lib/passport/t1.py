from dataclasses import dataclass, field, astuple, asdict
from collections.abc import MutableSequence
from enum import StrEnum


class GroupTypes(StrEnum):
    common = 'Направление'
    vehicle = 'Транспортное'
    pedestrian = 'Пешеходное'
    arrow = 'Поворотное'


class _Group:
    def __init__(
            self,
            index: int,
            num: str,
            name: str = GroupTypes.common,
            stages: str = '',
            traffic_lights = '',
            t_green_ext = 0,
            t_flashing_green = 0,
            t_yellow = 0,
            t_red = 0,
            t_red_yellow = 0,
            t_z = 0,
            t_zz = 0,
            all_red = False,
            toov_red = False,
            toov_green = False,
            description = ''
    ):
        self._errors = []
        self._raw_num = num
        self._name = name
        self._index = index
        self._is_float = len(num.split('.')) > 1
        try:
            self._num = float(num) if self._is_float else int(num)
        except ValueError:
            self._errors.append('Номер направления должен быть целым или вещественным числом.')
        self._stages = stages.split(',')
        self._traffic_lights = traffic_lights
        self._t_green_ext = t_green_ext
        self._t_flashing_green = t_flashing_green
        self._t_yellow = t_yellow
        self._t_red = t_red
        self._t_red_yellow = t_red_yellow
        self._t_z = t_z
        self._t_zz = t_zz
        self._all_red = all_red
        self._toov_red = toov_red
        self._toov_green = toov_green
        self._description= description


@dataclass
class Group:
    index: int
    num_as_string: str
    num_as_float: float = .0
    errors: MutableSequence = field(default_factory=list)
    name: str = str(GroupTypes.common)
    stages: str = ''
    traffic_lights: str = ''
    t_green_ext: int = 0
    t_flashing_green: int = 0
    t_yellow: int = 0
    t_red: int = 0
    t_red_yellow: int = 0
    t_z: int = 0
    t_zz: int = 0
    all_red: bool = False
    toov_red: bool = False
    toov_green: bool = False
    description: str = ''

    def __post_init__(self):
        try:
            self.num_as_float: float = float(self.num_as_string)
        except ValueError:
            self.num_as_float = .0
            self.errors.append('Номер направления должен быть целым или вещественным числом.')

    def __iter__(self):
        return (prop for prop in astuple(self)[1:])

    def is_valid(self) -> bool:
        return not bool(self.errors)


if __name__ == '__main__':
    test_group = Group(0, '1')



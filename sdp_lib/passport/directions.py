import re
from collections import Counter
from collections.abc import MutableSequence
from dataclasses import (
    dataclass,
    field,
    astuple,
    InitVar
)

from sdp_lib.passport.constants import GroupTypes


@dataclass
class Direction:

    ALL_RED = re.compile(r'кр|\-', re.IGNORECASE)
    ALL_TABLE_COLUMNS = slice(1, 15)
    FIRST_3_TABLE_COLUMNS = slice(1, 4)

    index: int
    num_as_string: str
    entity: str = str(GroupTypes.common)
    stages: str = ''
    traffic_lights: str = ''
    t_green_ext: int = 0
    t_flashing_green: int = 0
    t_yellow: int = 0
    t_red: int = 0
    t_red_yellow: int = 0
    t_z: int = 0
    t_zz: int = 0
    all_red: bool | None = None
    toov_red: bool = False
    toov_green: bool = False
    description: str = ''
    compute_num_as_float: InitVar[bool] = True
    num_as_float: float = .0
    errors: MutableSequence = field(default_factory=list)
    stages_as_list: MutableSequence[str] = field(default_factory=list)

    def __post_init__(self, compute_num_as_float: bool):
        if not self.num_as_string:
            self.add_errors(
                f'Нет данных о направлении с индексом={self.index}. '
                f'У направления должен быть номер, тип и фазы, в которых оно участвует.'
            )
            return
        if compute_num_as_float:
            try:
                self.num_as_float: float = float(self.num_as_string)
            except ValueError:
                self.errors.append('Номер направления должен быть целым или вещественным числом.')
        if self.all_red is None: # Определить, если параметр не задан явно при инициализации
            self.all_red = bool(re.findall(self.ALL_RED, self.stages))
        if not self.all_red:
            self.stages_as_list = self.stages.split(',') if self.stages else []

    def __iter__(self):
        return (prop for prop in astuple(self)[self.ALL_TABLE_COLUMNS])

    def add_errors(self, *args: str):
        for err in args:
            if err:
                self.errors.append(err)

    def is_valid(self) -> bool:
        return not bool(self.errors)


class DirectionsTable:
    def __init__(self, raw_directions: str):
        self._raw_groups = raw_directions
        self._directions: MutableSequence[Direction] = []
        self._errors = []
        self._max_direction_num: float = .0
        self._create_data_from_raw_directions_string()
        self._direction_type_counter = Counter(str(direction_type.entity) for direction_type in self._directions)

    def _add_errors(self, *args: str):
        for err in args:
            if err:
                self._errors.append(err)

    def _collect_errors_from_directions(self):
        for direction in self._directions:
            self._add_errors(*direction.errors)

    def _create_data_from_raw_directions_string(self):
        self._max_direction_num = .0
        for i, g in enumerate(self._raw_groups.split('\n')):
            # print(f'g: {g}')
            split_data = g.split()
            if not g:
                num = entity = stages = ''
            elif len(split_data) == 3:
                num, entity, stages = split_data
            elif len(split_data) == 1:
                num = 'xx'
                entity = GroupTypes.common
                stages = split_data[0]
            else:
                raise ValueError
            direction = Direction(index=i, num_as_string=num, entity=entity, stages=stages)
            self._max_direction_num = max(self._max_direction_num, direction.num_as_float)
            self._add_errors(*direction.errors)
            self._directions.append(direction)

    def get_errors(self) -> MutableSequence[str]:
        return self._errors

    def get_directions(self) -> MutableSequence[Direction]:
        return self._directions

    def get_max_direction_num(self) -> float:
        if self._max_direction_num.is_integer():
            return int(self._max_direction_num)
        return self._max_direction_num

    def get_direction_types_cnt(self):
        return self._direction_type_counter


def build_instances_groups_table(data: str):
    storage: MutableSequence[Direction] = []
    errors: MutableSequence[str] = []
    for i, g in enumerate(data.split('\n')):
        # print(f'g: {g}')
        split_data = g.split()
        if not g:
            errors.append(f'Нет данных о группе. Индекс={i} {g}')
            continue

        if len(split_data) == 3:
            num, entity, stages = split_data
        elif len(split_data) == 1:
            num = 'xx'
            entity = GroupTypes.common
            stages = split_data[0]
        else:
            raise ValueError
        storage.append(Direction(index=i, num_as_string=num, entity=entity, stages=stages))
        print(storage[i])
    # print(f'storage: \n', storage)
    # print()
    # print(f'errors: \n', errors)


if __name__ == '__main__':
    _data = '1\tТранспортное\t1,8,9\n2\tТранспортное\t1,2\n3\tТранспортное\t4\n4\tПоворотное\t2,3,4\n5\tТранспортное\t3,6,7,8,9,10\n6\tТранспортное\t5,6,7,10\n7\tТранспортное\t4,5,8,9\n8\tТранспортное\t1,2,3,4\n9\tПешеходное\t2,3\n10\tТранспортное\t1,5,6,7,8,9,10\n11\tПешеходное\t1,2,3,4,5,6,8,9\n12\tТранспортное\t2,3,4,5,6,7,10\n13\tТранспортное\t6,7,10\n14\tТранспортное\t1\n15\tПоворотное\t5,6,7,10\n16\tТранспортное\t5,6,7,8,9,10\n17\tТранспортное\t2,3,4\n18\tТранспортное\t7,10\n19\tТранспортное\t3,4,5,8,9,10\n20\tПешеходное\t3\n21\tТранспортное\t1,2,3,4\n22\tПешеходное\t1,2,3,4,5,8,9\n23\tТранспортное\t6,7\n24\tТранспортное\tПост.краси.\n'.rstrip()
    direction_table = DirectionsTable(_data)
    print(direction_table.get_max_direction_num())
    print(direction_table.get_errors())
    print(direction_table.get_direction_types_cnt())

    grp = Direction(0, '12', entity=GroupTypes.vehicle, stages='1,3,4,43')
    print(grp)

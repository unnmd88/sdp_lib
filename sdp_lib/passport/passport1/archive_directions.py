import re
from collections import Counter
from collections.abc import MutableSequence, MutableMapping
from dataclasses import (
    dataclass,
    field,
    astuple,
    InitVar
)
from typing import TypeAlias

from sdp_lib.passport.constants import DirectionEntities


DEBUG = True

stages_content_type: TypeAlias = MutableMapping[float, set[float]]


@dataclass
class StagesData:
    direction_to_stages_mapping: stages_content_type = field(default_factory=dict)
    stage_to_direction_mapping: stages_content_type = field(default_factory=dict)

    def load_groups_to_stages_mapping(self, direction_to_stages:  stages_content_type):
        print(f'self.direction_to_stages_mapping before: {self.direction_to_stages_mapping}')
        self.direction_to_stages_mapping |= direction_to_stages
        print(f'self.direction_to_stages_mapping after: {self.direction_to_stages_mapping}')
        print(f'self.stage_to_direction_mapping before: {self.stage_to_direction_mapping}')
        self.stage_to_direction_mapping.clear()
        for direction, stages in self.direction_to_stages_mapping.items():
            for stage in stages:
                try:
                    self.stage_to_direction_mapping[stage].add(direction)
                except KeyError:
                    self.stage_to_direction_mapping[stage] = {direction}
        print(f'self.stage_to_direction_mapping after: {self.stage_to_direction_mapping}')

    def load_stage_to_groups_mapping(self,  stage_to_direction:  MutableMapping[float, MutableSequence[float]]):
        self.stage_to_direction_mapping |= stage_to_direction
        for stage, directions in self.stage_to_direction_mapping.items():
            pass


@dataclass
class Direction:

    ALL_RED = re.compile(r'кр|\-', re.IGNORECASE)
    ALL_TABLE_COLUMNS = slice(1, 15)
    FIRST_3_TABLE_COLUMNS = slice(1, 4)

    index: int
    num_as_string: str
    entity: str = str(DirectionEntities.common)
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
    num_as_int_or_float: int | float = .0
    errors: MutableSequence = field(default_factory=list)
    stages_as_str: MutableSequence[str] = field(default_factory=list)
    stages_as_float: set[float] = field(default_factory=set)

    def __post_init__(self, compute_num_as_float: bool):
        if not self.num_as_string:
            self._add_errors(
                f'Нет данных о направлении с индексом={self.index}. '
                f'У направления должен быть номер, тип и фазы, в которых оно участвует.'
            )
            return
        if compute_num_as_float:
            try:
                self.num_as_int_or_float = int(self.num_as_string) if self.num_as_string.isdigit() else float(self.num_as_string)
            except ValueError:
                self.errors.append(
                    'Недопустимый номер направления. Допускаются номера в виде целых чисел("1", "5", "15" и т.д) или'
                    'числа через точку("8.1", "8.2", "10.1" и т.д.)'
                )
        if self.all_red is None: # Определить атрибут self.all_red, если он не задан явно при инициализации
            self.all_red = bool(re.findall(self.ALL_RED, self.stages))
        if not self.all_red: # Сформировать фазы для направления
            self._create_stages_data()

    def __iter__(self):
        return (prop for prop in astuple(self)[self.ALL_TABLE_COLUMNS])

    def _create_stages_data(self):
        self.stages_as_str = self.stages.split(',') if self.stages else []
        for stage in self.stages_as_str:
            try:
                stage = int(stage) if stage.isdigit() else float(stage)
                self.stages_as_float.add(stage)
            except ValueError:
                self._add_errors(f'Недопустимое представление фазы: {stage}')
        try:
            assert len(self.stages_as_float) == len(self.stages_as_str)
        except AssertionError:
            self.stages_as_float.clear()

    def _add_errors(self, *args: str):
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
        self._max_stage: float = .0
        self._stages_data = StagesData()
        self._create_data_from_raw_directions_string()
        self._direction_type_counter = Counter(str(direction_type.entity) for direction_type in self._directions)

    def _add_errors(self, *args: str):
        for err in args:
            if err:
                self._errors.append(err)

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
                entity = DirectionEntities.common
                stages = split_data[0]
            else:
                raise ValueError
            direction = Direction(index=i, num_as_string=num, entity=entity, stages=stages)
            self._add_errors(*direction.errors)
            if not self._errors:
                self._max_direction_num = max(self._max_direction_num, direction.num_as_int_or_float)
                if not direction.all_red:
                    self._max_stage = max(self._max_stage, max(direction.stages_as_float))
            self._directions.append(direction)
        example = {d.num_as_int_or_float: d.stages_as_float for d in self._directions}
        self._stages_data.load_groups_to_stages_mapping(example)

    def get_errors(self) -> MutableSequence[str]:
        return self._errors

    def get_directions(self) -> MutableSequence[Direction]:
        return self._directions

    def get_max_direction_num(self) -> float:
        return self._max_direction_num

    def get_max_stage_num(self) -> float:
        return self._max_direction_num

    def get_direction_types_cnt(self):
        return self._direction_type_counter

    def build_table_stages(self):
        pass


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
            entity = DirectionEntities.common
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
    _data2 = '1\t1, 2, 8, 10, 11, 14, 21, 22\n2\t2, 4, 8, 9, 11, 12, 17, 22, 25\n3\t4, 5, 8, 9, 11, 12, 17, 19, 20, 21, 22\n4\t3, 4, 7, 8, 11, 12, 17, 19, 21, 22\n5\t6, 7, 10, 11, 12, 15, 16, 19, 22\n6\t5, 6, 10, 11, 12, 13, 15, 16, 23, 25\n7\t5, 6, 10, 12, 13, 15, 16, 18, 23, 25\n8\t1, 5, 7, 10, 11, 16, 19, 22\n9\t1, 5, 7, 10, 11, 16, 19, 22\n10\t5, 6, 10, 12, 13, 15, 16, 18, 19\n'.rstrip()

    direction_table = DirectionsTable(_data)
    print(direction_table.get_max_direction_num())
    print(direction_table.get_errors())
    print(direction_table.get_direction_types_cnt())
    print(direction_table.get_max_stage_num())

    grp = Direction(0, '12', entity=DirectionEntities.vehicle, stages='1,3,4,43')
    print(grp)

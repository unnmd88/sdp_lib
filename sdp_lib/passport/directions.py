import pprint
import re
import time
from collections import Counter
from collections.abc import MutableSequence, MutableMapping, Sequence

from sdp_lib.passport.base import AbstractRow, ColumnValues, AbstractTable
from sdp_lib.passport.constants import (
    DirectionTypes,
    StagesMapping,
    ColumnsDirectionTimes,
    default_values
)
from sdp_lib.passport.mixins import ReprMixin

from sdp_lib.passport.utils import StagesData


DEBUG = True


class DirectionRaw(AbstractRow, ReprMixin):

    ALL_RED = re.compile(r'кр|-', re.IGNORECASE)
    ALL_TABLE_COLUMNS = slice(1, 15)
    FIRST_3_TABLE_COLUMNS = slice(1, 4)

    def __init__(
            self,
            index: int,
            num_as_string: str,
            entity: str = str(DirectionTypes.common),
            stages: str = '',
            traffic_lights: str = '' ,
            t_green_ext: int = None,
            t_flashing_green: int = None,
            t_yellow: int = None,
            t_red: int = None,
            t_red_yellow: int = None,
            t_z: int = None,
            t_zz: int = None,
            all_red: bool = None,
            toov_red: bool = None,
            toov_green: bool = None,
            description: str = '',
    ):
        super().__init__()
        self.index = index
        self.num_as_string = num_as_string
        self.entity = entity
        self.stages = stages
        self.traffic_lights = traffic_lights
        self.t_green_ext = self._get_default_val(ColumnsDirectionTimes.t_green_ext, t_green_ext)
        self.t_flashing_green = self._get_default_val(ColumnsDirectionTimes.t_flashing_green, t_flashing_green)
        self.t_yellow =  self._get_default_val(ColumnsDirectionTimes.t_yellow, t_yellow)
        self.t_red = self._get_default_val(ColumnsDirectionTimes.t_red, t_red)
        self.t_red_yellow = self._get_default_val(ColumnsDirectionTimes.t_red_yellow, t_red_yellow)
        self.t_z =  self._get_default_val(ColumnsDirectionTimes.t_z, t_z)
        self.t_zz =  self._get_default_val(ColumnsDirectionTimes.t_zz, t_zz)
        self.always_red = all_red
        self.toov_red = toov_red or False
        self.toov_green= toov_green or False
        self.description = description
        self.stages_as_str: MutableSequence[str] = []
        self.stages_as_float: set[float] = set()
        self._allow_for_compare_stages = False
        self._entity_is_standard = False
        self._extra_init_and_check_data()

    def _get_default_val(self, col_name: ColumnsDirectionTimes, init_val) -> ColumnValues:
        default_val = default_values.get((self.entity, col_name))
        if init_val is None:
            val = default_val
        else:
            val = init_val
        return ColumnValues(col_name, init_val, default_val, val)

    def _validate_entity(self) -> bool:
        try:
            return bool(DirectionTypes(self.entity))
        except ValueError:
            self.add_warnings(
                f'Задан нестандартный тип направления: {self.entity}. '
                f'Стандартные типы: {[str(direction) for direction in DirectionTypes]}'
            )
            return False

    def _extra_init_and_check_data(self):
        self._entity_is_standard = self.entity_is_standard
        if not self.num_as_string:
            self.add_errors(
                f'Нет данных о направлении с индексом={self.index}. '
                f'У направления должен быть номер, тип и фазы, в которых оно участвует.'
            )
            return
        try:
            if self.num_as_string.isdigit():
                self.num_as_int_or_float = int(self.num_as_string)
            else:
                self.num_as_int_or_float = float(self.num_as_string)
            assert self.num_as_string == str(self.num_as_int_or_float)
        except (ValueError, AssertionError):
            self.add_errors(
                f'Недопустимый номер направления "{self.num_as_string}"(Индекс={self.index}). '
                f'Допускаются номера в виде целых чисел("1", "5", "15" и т.д) или '
                f'числа через точку("8.1", "8.2", "10.1" и т.д.)'
            )
        if self.always_red is None: # Определить атрибут self.all_red, если он не задан явно при инициализации
            self.always_red = bool(re.findall(self.ALL_RED, self.stages))
        if not self.always_red: # Сформировать фазы для направления
            self._create_stages_data()
        # self._allow_for_compare_stages = self._validate_for_allow_to_compare_stages()
        #TO DO валидация типов остальных атрибутов

    def _create_stages_data(self):
        self.stages_as_str = self.stages.split(',') if self.stages else []
        for stage in self.stages_as_str:
            try:
                stage = int(stage) if stage.isdigit() else float(stage)
                self.stages_as_float.add(stage)
            except ValueError:
                self.add_errors(f'Недопустимое представление фазы: {stage}')
        try:
            assert len(self.stages_as_float) == len(self.stages_as_str)
        except AssertionError:
            self.stages_as_float.clear()

    @property
    def entity_is_standard(self) -> bool:
        try:
            self._entity_is_standard = bool(DirectionTypes(self.entity))
        except ValueError:
            self._entity_is_standard = False
        return self._entity_is_standard

    @property
    def allow_for_compare_stages(self):
        if not self._errors and not self.always_red and self.stages_as_float:
            self._allow_for_compare_stages = True
        elif not self._errors and self.always_red:
            self._allow_for_compare_stages = True
        else:
            self._allow_for_compare_stages = False
        return self._allow_for_compare_stages


class DirectionsTable(AbstractTable, ReprMixin):
    def __init__(self, raw_directions: str):
        super().__init__(raw_directions)
        self._max_direction_num: float = .0
        self._max_stage: float = .0
        self._quantity_directions_with_err_for_compare_stages = 0
        self._stages_data = StagesData(StagesMapping.direction_to_stages)
        self._create_data_from_raw_directions_string()
        self._direction_type_counter = Counter(str(direction.entity) for direction in self._rows.values())
        self._valid_to_compare_stages = True

    def _create_data_from_raw_directions_string(self):
        self._max_direction_num = .0
        for i, g in enumerate(self._raw_data.split('\n')):
            # print(f'g: {g}')
            split_data = g.split()
            if not g:
                num = entity = stages = ''
            elif len(split_data) == 3:
                num, entity, stages = split_data
            elif len(split_data) == 1:
                num = 'xx'
                entity = DirectionTypes.common
                stages = split_data[0]
            else:
                raise ValueError
            direction = DirectionRaw(index=i, num_as_string=num, entity=entity, stages=stages)
            # print(direction)
            if not direction.get_errors():
                self._max_direction_num = max(self._max_direction_num, direction.num_as_int_or_float)
                if not direction.always_red:
                    self._max_stage = max(self._max_stage, max(direction.stages_as_float))
            else:
                self._load_row_with_err((i, direction))
            if not direction.allow_for_compare_stages:
                self._quantity_directions_with_err_for_compare_stages += 1
            self._load_row((direction.num_as_int_or_float, direction))
        self._stages_data.refresh({d.num_as_int_or_float: d.stages_as_float for d in self._rows.values()})

    def get_max_direction_num(self) -> float:
        return self._max_direction_num

    def get_max_stage_num(self) -> float:
        return self._max_direction_num

    def get_direction_types_cnt(self):
        return self._direction_type_counter

    def get_stages_data(self) -> StagesData:
        return self._stages_data

    @property
    def quantity_directions_with_err_for_compare_stages(self):
        return self._quantity_directions_with_err_for_compare_stages


if __name__ == '__main__':
    _data = '1\tТранспортное\t1,8,9\n2\tТранспортное\t1,2\n3\tТранспортное\t4\n4\tПоворотное\t2,3,4\n5е\tТранспортное\t3,6,7,8,9,10\n6\tТранспортное\t5,6,7,10\n7\tТранспортное\t4,5,8,9\n8\tТранспортное\t1,2,3,4\n9\tПешеходное\t2,3\n10\tТранспортное\t1,5,6,7,8,9,10\n11\tПешеходное\t1,2,3,4,5,6,8,9\n12\tТранспортное\t2,3,4,5,6,7,10\n13\tТранспортное\t6,7,10\n14\tТранспортное\t1\n15\tПоворотное\t5,6,7,10\n16\tТранспортное\t5,6,7,8,9,10\n17\tТранспортное\t2,3,4\n18\tТранспортное\t7,10\n19\tТранспортное\t3,4,5,8,9,10\n20\tПешеходное\t3\n21\tТранспортное\t1,2,3,4\n22\tПешеходное\t1,2,3,4,5,8,9\n23\tТранспортное\t6,7\n24\tТранспортное\tПост.краси.\n'.rstrip()
    _data2 = '1\t1, 2, 8, 10, 11, 14, 21, 22\n2\t2, 4, 8, 9, 11, 12, 17, 22, 25\n3\t4, 5, 8, 9, 11, 12, 17, 19, 20, 21, 22\n4\t3, 4, 7, 8, 11, 12, 17, 19, 21, 22\n5\t6, 7, 10, 11, 12, 15, 16, 19, 22\n6\t5, 6, 10, 11, 12, 13, 15, 16, 23, 25\n7\t5, 6, 10, 12, 13, 15, 16, 18, 23, 25\n8\t1, 5, 7, 10, 11, 16, 19, 22\n9\t1, 5, 7, 10, 11, 16, 19, 22\n10\t5, 6, 10, 12, 13, 15, 16, 18, 19\n'.rstrip()

    start_time = time.perf_counter()
    grp = DirectionRaw(0, '12', entity=DirectionTypes.vehicle, stages='1,3,4,43')
    print(grp)
    direction_table = DirectionsTable(_data)
    print(direction_table)
    print(f'direction_table.quantity_directions_with_err_for_compare_stages: {direction_table.quantity_directions_with_err_for_compare_stages}')
    pprint.pprint(direction_table.get_all_rows())
    print('-*-' * 100)
    pprint.pprint(direction_table.get_rows_with_errors())
    print(f'Время составило: {time.perf_counter() - start_time}')
    print(direction_table.get_all_rows()[6])
    # pprint.pprint(direction_table.get_stages_data().get_direction_to_stages_mapping())
    # pprint.pprint(direction_table.get_stages_data().get_stage_to_direction_mapping())



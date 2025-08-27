import json
import logging
import re
import time
from collections import Counter
from functools import cached_property

from sdp_lib.passport.base import (
    AbstractTableWithStages,
    Cell,
    StageOrDirectionCell,
    get_number_cell_data,
    get_cell,
    Message,
    AbstractRow,
)
from sdp_lib.passport.constants import (
    DirectionTypes,
    ColNamesDirectionsTable,
    default_values,
    StorageNames,
    TableNames,
    RowNames,
    MessageCategories,
    Fields
)
from sdp_lib.passport.mixins import ReprMixin
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import read_file_as_string
from sdp_lib.passport import logging_config


DEBUG = True

logger = logging.getLogger(__name__)


class DirectionRow(AbstractRow):

    name = RowNames.direction

    ALWAYS_RED = re.compile(r'кр|-', re.IGNORECASE)
    ALL_TABLE_COLUMNS = slice(1, 15)
    FIRST_3_TABLE_COLUMNS = slice(1, 4)

    def __init__(
            self,
            index: int,
            number: str | int | float,
            direction_type: str = str(DirectionTypes.common),
            stages: str = '',
            traffic_lights: str = '' ,
            t_green_ext: int = None,
            t_flashing_green: int = None,
            t_yellow: int = None,
            t_red: int = None,
            t_red_yellow: int = None,
            t_z: int = None,
            t_zz: int = None,
            toov_red: bool = None,
            toov_green: bool = None,
            description: str = '',
    ):
        super().__init__()
        self._extra_data.err_and_warn.set_name(StorageNames.direction)
        self.index = index
        self.number = get_number_cell_data(number, ColNamesDirectionsTable.number)
        if not self.number.is_valid:
            self._extra_data.err_and_warn.add_errors(
                Message(Text.get_bad_num(number, ColNamesDirectionsTable.number), MessageCategories.validation),
            )
            self._extra_data.permissions.set_val_for_compare_stages(False)
        self.direction_type = self._get_direction_type(direction_type)
        self.stages = StageOrDirectionCell(stages)
        if not self.stages.is_valid:
            self._extra_data.err_and_warn.add_errors(
                Message(Text.get_bad_val(stages, ColNamesDirectionsTable.stages), MessageCategories.validation)
            )
            self._extra_data.permissions.set_val_for_compare_stages(False)
        self.traffic_lights = get_cell(ColNamesDirectionsTable.traffic_lights, traffic_lights)
        self.t_green_ext = self._get_prom_tact_time(ColNamesDirectionsTable.t_green_ext, t_green_ext)
        self.t_flashing_green = self._get_prom_tact_time(ColNamesDirectionsTable.t_flashing_green, t_flashing_green)
        self.t_yellow =  self._get_prom_tact_time(ColNamesDirectionsTable.t_yellow, t_yellow)
        self.t_red = self._get_prom_tact_time(ColNamesDirectionsTable.t_red, t_red)
        self.t_red_yellow = self._get_prom_tact_time(ColNamesDirectionsTable.t_red_yellow, t_red_yellow)
        self.t_z =  self._get_prom_tact_time(ColNamesDirectionsTable.t_z, t_z)
        self.t_zz =  self._get_prom_tact_time(ColNamesDirectionsTable.t_zz, t_zz)
        self.always_red = self.stages.is_always_red
        self.toov_red = get_cell(ColNamesDirectionsTable.toov_red, toov_red)
        self.toov_green= get_cell(ColNamesDirectionsTable.toov_green, toov_green)
        self.description = get_cell(ColNamesDirectionsTable.description, description, '')

    def _get_direction_type(self, init_val: str | DirectionTypes) -> Cell:
        default_val, is_valid = DirectionTypes.common, True
        if re.findall(self.ALWAYS_RED, init_val):
            val = DirectionTypes.always_red
        elif init_val:
            val = init_val
            try:
                DirectionTypes(init_val)
            except ValueError:
                is_valid = False
                self._extra_data.err_and_warn.add_warnings(
                    Message(
                        f'Задан нестандартный тип направления: {init_val}. '
                        f'Стандартные типы: {DirectionTypes.get_standard_types()}',
                        MessageCategories.validation
                    )
                )
        else:
            val = default_val
        return Cell(ColNamesDirectionsTable.direction_type, init_val, default_val, val, is_valid)

    def _get_prom_tact_time(self, col_name: ColNamesDirectionsTable, init_val) -> Cell:
        default_val = default_values.get((self.direction_type, col_name))
        if init_val is None:
            val = default_val
        else:
            val = init_val
        return Cell(col_name, init_val, default_val, val)

    @cached_property
    def direction_type_is_standard(self) -> bool:
        try:
            return bool(DirectionTypes(self.direction_type.value))
        except ValueError:
            return False

    # def dump_to_dict(self):
    #     return {
    #         str(Fields.index): self.index,
    #         str(Fields.number): self.number._asdict(),
    #         str(Fields.direction): self.direction_type._asdict(),
    #         str(Fields.stages): {
    #             str(Fields.cell_value): self.stages.get_stages_or_directions_string_row(),
    #             str(Fields.bad_nums): self.stages.get_bad_nums(),
    #             str(Fields.doubles): self.stages.get_doubles(),
    #             str(Fields.asc_order): self.stages.is_asc_order,
    #             str(Fields.formatted_string): self.stages.get_numbers_as_str(),
    #             str(Fields.is_always_red): self.stages.is_always_red
    #         },
    #         str(Fields.traffic_lights): self.traffic_lights._asdict(),
    #         str(Fields.t_green_ext): self.t_green_ext._asdict(),
    #         str(Fields.t_green_flashing): self.t_flashing_green._asdict(),
    #         str(Fields.t_yellow): self.t_yellow._asdict(),
    #         str(Fields.t_red): self.t_red._asdict(),
    #         str(Fields.t_red_yellow): self.t_red_yellow._asdict(),
    #         str(Fields.t_z): self.t_z._asdict(),
    #         str(Fields.t_zz): self.t_zz._asdict(),
    #         str(Fields.always_red): self.stages.is_always_red,
    #         str(Fields.toov_green): self.toov_green._asdict(),
    #         str(Fields.toov_red): self.toov_red._asdict(),
    #         str(Fields.description): self.description._asdict(),
    #         str(Fields.errors): self.data.err_and_warn.get_errors_by_categories()
    #     }


class DirectionsTable(AbstractTableWithStages, ReprMixin):

    name = TableNames.directions_table
    allowed_cnt_row_props = {1, 3, 14, 15}
    row_class = DirectionRow
    key_name = Fields.directions

    def __init__(self, income_data: str):
        super().__init__(income_data)
        self._direction_type_counter = Counter(str(direction.direction_type.value) for direction in self._rows)

    def get_direction_types_cnt(self):
        return self._direction_type_counter

    def dump_to_dict(self) -> dict:
        return super().dump_to_dict() | {
            str(Fields.directions_by_type): {k: v for k, v in self._direction_type_counter.items()}
        }


def display_directions(raw_data: str = None) -> DirectionsTable:
    if raw_data is None:
        raw_data = '1\tТранспортное\t1,8,1,9\n2\tТранспортное\t1,2\n3\tТранспортное\t4\n4\tПоворотное\t2,3,4\n5\tТранспортное\t3,6,7,8,9,10\n6\tТранспортное\t5,6,7,10\n7\tТранспортное\t4,5,8,9\n8\tТранспортное\t1,2,3,4\n9\tПешеходное\t2,3\n10\tТранспортное\t1,5,6,7,8,9,10\n11\tПешеходное\t1,2,3,4,5,6,8,9\n12\tТранспортное\t2,3,4,5,6,7,10\n13\tТранспортное\t6,7,10\n14\tТранспортное\t1\n15\tПоворотное\t5,6,7,10\n16\tТранспортное\t5,6,7,8,9,10\n17\tТранспортное\t2,3,4\n18\tТранспортное\t7,10\n19\tТранспортное\t3,4,5,8,9,10\n20\tПешеходное\t3\n21\tТранспортное\t1,2,3,4\n22\tПешеходное\t1,2,3,4,5,8,9\n23\tТранспортное\t6,7\n24\tТранспортное\tПост.краси.\n'.rstrip()
    start_time = time.perf_counter()
    grp = DirectionRow(0, '12s', direction_type='Пост красн.', stages='1,3,4,43')
    print(grp.extra_data.err_and_warn.get_errors_by_categories())
    logger.debug(grp)
    print('-*-' * 100)
    directions_table = DirectionsTable(raw_data)
    # print(directions_table)
    for k, v in directions_table.rows().items():
        print(f'num: {k}, instance: {v}')
    # for k, v in itertools.chain(directions_table.get_stages_data().get_direction_to_stages_mapping().items(),
    #                              directions_table.get_stages_data().get_stage_to_direction_mapping().items()):
    #     print(f'{k:<4}: {v}')
    for d in directions_table:
        print(json.dumps(d.as_dict(), indent=4, ensure_ascii=False))
        if d.number.value == 1:
            with open('example_direction_as_json.json', 'w', encoding='utf-8') as f:
                f.write(json.dumps(d.as_dict(), indent=4, ensure_ascii=False))

    print(f'Время составило: {time.perf_counter() - start_time}')

    return directions_table



if __name__ == '__main__':
    _data2 = '1\t1, 2, 8, 10, 11, 14, 21, 22\n2\t2, 4, 8, 9, 11, 12, 17, 22, 25\n3\t4, 5, 8, 9, 11, 12, 17, 19, 20, 21, 22\n4\t3, 4, 7, 8, 11, 12, 17, 19, 21, 22\n5\t6, 7, 10, 11, 12, 15, 16, 19, 22\n6\t5, 6, 10, 11, 12, 13, 15, 16, 23, 25\n7\t5, 6, 10, 12, 13, 15, 16, 18, 23, 25\n8\t1, 5, 7, 10, 11, 16, 19, 22\n9\t1, 5, 7, 10, 11, 16, 19, 22\n10\t5, 6, 10, 12, 13, 15, 16, 18, 19\n'.rstrip()

    display_directions(read_file_as_string('directions_example'))

    # print(json.dumps(asdict(obj), indent=4, ensure_ascii=False))






import logging
import re
from collections import Counter
from dataclasses import dataclass

from sdp_lib.passport.passport1.base import (
    AbstractTableWithStages,
    Cell,
    StageOrDirectionCell,
    get_cell_with_value_as_number_,
    get_cell,
    Message,
    AbstractRow, get_cell_with_value_as_prom_tact_time,
)
from sdp_lib.passport.constants import (
    DirectionEntities,
    ColNamesDirectionsTable,
    StorageNames,
    TableNames,
    RowNames,
    MessageCategories,
    Fields
)
from sdp_lib.passport.mixins import ReprMixin
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import read_file_as_string, timed, to_json

DEBUG = True

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DirectionRowCells:
    number: Cell
    direction_type: Cell
    stages: StageOrDirectionCell
    traffic_lights: Cell
    t_green_ext: Cell
    t_flashing_green: Cell
    t_yellow: Cell
    t_red: Cell
    t_red_yellow: Cell
    t_z: Cell
    t_zz: Cell
    always_red: Cell
    toov_red: Cell
    toov_green: Cell
    description: Cell


class DirectionRow(AbstractRow, ReprMixin):

    name = RowNames.direction

    ALWAYS_RED = re.compile(r'кр|-', re.IGNORECASE)
    ALL_TABLE_COLUMNS = slice(1, 15)
    FIRST_3_TABLE_COLUMNS = slice(1, 4)

    def __init__(
            self,
            index: int,
            number: str | int | float,
            direction_type: str = str(DirectionEntities.common),
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
        super().__init__(index)
        self._extra_data.err_and_warn.set_name(StorageNames.direction)
        _stages = StageOrDirectionCell(stages)
        dt = self._get_direction_type(direction_type)
        dt_val = dt.value
        self._cells = DirectionRowCells(
            get_cell_with_value_as_number_(number, ColNamesDirectionsTable.number),
            dt,
            _stages,
            get_cell(ColNamesDirectionsTable.traffic_lights, traffic_lights),
            get_cell_with_value_as_prom_tact_time(dt_val, ColNamesDirectionsTable.t_green_ext, t_green_ext),
            get_cell_with_value_as_prom_tact_time(dt_val, ColNamesDirectionsTable.t_flashing_green, t_flashing_green),
            get_cell_with_value_as_prom_tact_time(dt_val, ColNamesDirectionsTable.t_yellow, t_yellow),
            get_cell_with_value_as_prom_tact_time(dt_val, ColNamesDirectionsTable.t_red, t_red),
            get_cell_with_value_as_prom_tact_time(dt_val, ColNamesDirectionsTable.t_red_yellow, t_red_yellow),
            get_cell_with_value_as_prom_tact_time(dt_val, ColNamesDirectionsTable.t_z, t_z),
            get_cell_with_value_as_prom_tact_time(dt_val, ColNamesDirectionsTable.t_zz, t_zz),
            get_cell(ColNamesDirectionsTable.always_red, _stages.is_always_red),
            get_cell(ColNamesDirectionsTable.toov_red, toov_red),
            get_cell(ColNamesDirectionsTable.toov_green, toov_green),
            get_cell(ColNamesDirectionsTable.description, description, '')

        )
        if not self.cells.number.ok:
            self._extra_data.err_and_warn.add_errors(
                Message(Text.get_bad_num(number, ColNamesDirectionsTable.number), MessageCategories.validation),
            )
            self._extra_data.permissions.set_val_for_compare_stages(False)
        if not self.cells.stages.ok:
            self._extra_data.err_and_warn.add_errors(
                Message(Text.get_bad_val(stages, ColNamesDirectionsTable.stages), MessageCategories.validation)
            )
            self._extra_data.permissions.set_val_for_compare_stages(False)

    def _get_direction_type(self, init_val: str | DirectionEntities) -> Cell:
        default_val, is_valid = DirectionEntities.common, True
        if re.findall(self.ALWAYS_RED, init_val):
            val = DirectionEntities.always_red
        elif init_val:
            val = init_val
            try:
                DirectionEntities(init_val)
            except ValueError:
                is_valid = False
                self._extra_data.err_and_warn.add_warnings(
                    Message(
                        f'Задан нестандартный тип направления: {init_val}. '
                        f'Стандартные типы: {DirectionEntities.get_standard_types()}',
                        MessageCategories.validation
                    )
                )
        else:
            val = default_val
        return Cell(ColNamesDirectionsTable.direction_entity, init_val, default_val, val, is_valid)

    def _check_direction_type_is_standard(self) -> bool:
        try:
            return bool(DirectionEntities(self.cells.direction_entity.value))
        except ValueError:
            self._extra_data.err_and_warn.add_warnings(
                Message('Задан нестандартный тип направления.', MessageCategories.validation)
            )
            return False


class DirectionsTable(AbstractTableWithStages, ReprMixin):

    name = TableNames.directions_table
    allowed_cnt_row_props = {1, 3, 14, 15}
    row_class = DirectionRow
    key_name = Fields.directions

    def __init__(self, income_data: str):
        super().__init__(income_data)
        self._direction_type_counter = Counter(str(row.cells.direction_type.value) for row in self._rows)

    def get_direction_types_cnt(self):
        return self._direction_type_counter

    def dump_to_dict(self) -> dict:
        return super().dump_to_dict() | {
            str(Fields.directions_by_type): {k: v for k, v in self._direction_type_counter.items()}
        }


@timed
def display_directions(raw_data: str = None) -> DirectionsTable:
    if raw_data is None:
        data_as_string = read_file_as_string('../_mock_data/directions_example1')
    else:
        data_as_string = raw_data
    grp = DirectionRow(0, '12s', direction_type='Пост красн.', stages='1,3,4,43')
    print(grp.extra_data.err_and_warn.get_errors_by_categories())
    logger.debug(grp)
    print('-*-' * 100)
    dt = DirectionsTable(data_as_string)
    print(to_json(dt.dump_to_dict(), 'directions_table_example'))
    return dt



if __name__ == '__main__':
    _data2 = '1\t1, 2, 8, 10, 11, 14, 21, 22\n2\t2, 4, 8, 9, 11, 12, 17, 22, 25\n3\t4, 5, 8, 9, 11, 12, 17, 19, 20, 21, 22\n4\t3, 4, 7, 8, 11, 12, 17, 19, 21, 22\n5\t6, 7, 10, 11, 12, 15, 16, 19, 22\n6\t5, 6, 10, 11, 12, 13, 15, 16, 23, 25\n7\t5, 6, 10, 12, 13, 15, 16, 18, 23, 25\n8\t1, 5, 7, 10, 11, 16, 19, 22\n9\t1, 5, 7, 10, 11, 16, 19, 22\n10\t5, 6, 10, 12, 13, 15, 16, 18, 19\n'.rstrip()

    display_directions()

    # print(json.dumps(asdict(obj), indent=4, ensure_ascii=False))






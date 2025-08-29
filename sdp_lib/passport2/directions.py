import re
from dataclasses import dataclass, make_dataclass
from enum import IntEnum, auto
from typing import NamedTuple

from sdp_lib.passport2.base import Cell, StageOrDirectionCell


class _Types(IntEnum):
    all_fields15 = 0
    exclude_tzz_fields14 = 1


def _get_fields(fields_type: _Types):
    all_fields = (
        ('number', Cell),
        ('direction_type', Cell),
        ('stages', StageOrDirectionCell),
        ('traffic_lights', Cell),
        ('t_green_ext', Cell),
        ('t_flashing_green', Cell),
        ('t_yellow', Cell),
        ('t_red', Cell),
        ('t_red_yellow', Cell),
        ('t_z', Cell),
        ('t_zz', Cell),
        ('always_red', Cell),
        ('toov_red', Cell),
        ('toov_green', Cell),
        ('description', Cell)
    )
    if fields_type == _Types.exclude_tzz_fields14:
        return tuple(f for f in all_fields if f[0] != 't_zz')
    return all_fields


DirectionRowCellsAll = make_dataclass(
    'DirectionRowCellsAll',
    _get_fields(_Types.all_fields15),
    slots=True,
    frozen=True
)


class DirectionRowCells(NamedTuple):
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


class DirectionRowCellsExcludeTzz(NamedTuple):
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
    always_red: Cell
    toov_red: Cell
    toov_green: Cell
    description: Cell


# @dataclass(frozen=True, slots=True)
# class DirectionRowCells:
#     number: Cell
#     direction_type: Cell
#     stages: StageOrDirectionCell
#     traffic_lights: Cell
#     t_green_ext: Cell
#     t_flashing_green: Cell
#     t_yellow: Cell
#     t_red: Cell
#     t_red_yellow: Cell
#     t_z: Cell
#     t_zz: Cell
#     always_red: Cell
#     toov_red: Cell
#     toov_green: Cell
#     description: Cell


class DirectionRow(AbstractRow, ReprMixin):

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
        if not self.cells.number.is_valid:
            self._extra_data.err_and_warn.add_errors(
                Message(Text.get_bad_num(number, ColNamesDirectionsTable.number), MessageCategories.validation),
            )
            self._extra_data.permissions.set_val_for_compare_stages(False)
        if not self.cells.stages.is_valid:
            self._extra_data.err_and_warn.add_errors(
                Message(Text.get_bad_val(stages, ColNamesDirectionsTable.stages), MessageCategories.validation)
            )
            self._extra_data.permissions.set_val_for_compare_stages(False)

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

    def _check_direction_type_is_standard(self) -> bool:
        try:
            return bool(DirectionTypes(self.cells.direction_type.value))
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

if __name__ == '__main__':
    print(DirectionRowCellsExcludeTzz(*['№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', '"Запрет"', '"Запрет"', '"Запрет"', '"Запрет"', '"Разрешение"', '"Разрешение"', 'Пост. красное', 'ТООВ ', 'ТООВ ', 'Примечание']))
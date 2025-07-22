import typing
from enum import StrEnum, IntEnum, auto, Enum


class DirectionTypes(StrEnum):
    common = 'Направление'
    vehicle = 'Транспортное'
    pedestrian = 'Пешеходное'
    arrow = 'Поворотное'


class StagesMapping(IntEnum):
    direction_to_stages = 0
    stage_to_direction  = 1


class ColumnsNamesDirectionTable(StrEnum):
    t_green_ext = 'Тзд'
    t_flashing_green = 'Тзм'
    t_yellow = 'Тж'
    t_red = 'Тк'
    t_red_yellow = 'Ткж'
    t_z = 'Тз'
    t_zz = 'Тз'


"""
class DefaultTimeValuesDirectionTable(typing.NamedTuple):
    t_green_ext: int
    t_flashing_green: int
    t_yellow: int
    t_red: int
    t_red_yellow: int
    t_z: int
    t_zz: int


vehicle_direction_default_times = DefaultTimeValuesDirectionTable(0, 3, 3, 0, 1, 0, 0)
pedestrian_direction_default_times = DefaultTimeValuesDirectionTable(0, 3, 0, 3, 0, 0, 0)
arrow_direction_default_times = DefaultTimeValuesDirectionTable(0, 3, 0, 3, 0, 0, 0)
common_direction_default_times = DefaultTimeValuesDirectionTable(0, 0, 0, 0, 0, 0, 0)
"""


default_values = {
    (DirectionTypes.vehicle, ColumnsNamesDirectionTable.t_green_ext): 0,
    (DirectionTypes.vehicle, ColumnsNamesDirectionTable.t_flashing_green): 3,
    (DirectionTypes.vehicle, ColumnsNamesDirectionTable.t_yellow): 3,
    (DirectionTypes.vehicle, ColumnsNamesDirectionTable.t_red): 0,
    (DirectionTypes.vehicle, ColumnsNamesDirectionTable.t_red_yellow): 1,
    (DirectionTypes.vehicle, ColumnsNamesDirectionTable.t_z): 0,
    (DirectionTypes.vehicle, ColumnsNamesDirectionTable.t_zz): 0,

    (DirectionTypes.pedestrian, ColumnsNamesDirectionTable.t_green_ext): 0,
    (DirectionTypes.pedestrian, ColumnsNamesDirectionTable.t_flashing_green): 3,
    (DirectionTypes.pedestrian, ColumnsNamesDirectionTable.t_yellow): 0,
    (DirectionTypes.pedestrian, ColumnsNamesDirectionTable.t_red): 3,
    (DirectionTypes.pedestrian, ColumnsNamesDirectionTable.t_red_yellow): 0,
    (DirectionTypes.pedestrian, ColumnsNamesDirectionTable.t_z): 0,
    (DirectionTypes.pedestrian, ColumnsNamesDirectionTable.t_zz): 0,

    (DirectionTypes.arrow, ColumnsNamesDirectionTable.t_green_ext): 0,
    (DirectionTypes.arrow, ColumnsNamesDirectionTable.t_flashing_green): 3,
    (DirectionTypes.arrow, ColumnsNamesDirectionTable.t_yellow): 0,
    (DirectionTypes.arrow, ColumnsNamesDirectionTable.t_red): 3,
    (DirectionTypes.arrow, ColumnsNamesDirectionTable.t_red_yellow): 0,
    (DirectionTypes.arrow, ColumnsNamesDirectionTable.t_z): 0,
    (DirectionTypes.arrow, ColumnsNamesDirectionTable.t_zz): 0,
}


if __name__ == '__main__':
    print()
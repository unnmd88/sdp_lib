from enum import (
    Enum,
    StrEnum,
    IntEnum,
    auto,

)


class MessageLevels(StrEnum):
    debug = 'DEBUG'
    info = 'INFO'
    warning = 'WARNING'
    error = 'ERROR'
    critical = 'CRITICAL'


class StorageNames(StrEnum):
    direction = 'Направление'
    directions_table = 'Таблица направлений'
    income_data = 'Входные данные'
    errors_and_warnings = 'Ошибки и предупреждения'


class DirectionTypes(StrEnum):
    common = 'Направление'
    vehicle = 'Транспортное'
    pedestrian = 'Пешеходное'
    arrow = 'Поворотное'
    always_red = 'Пост. красн'


class StagesMapping(IntEnum):
    direction_to_stages = 0
    stage_to_direction  = 1


class ColNamesDirectionsTable(StrEnum):
    t_green_ext = 'Тзд'
    t_flashing_green = 'Тзм'
    t_yellow = 'Тж'
    t_red = 'Тк'
    t_red_yellow = 'Ткж'
    t_z = 'Тз'
    t_zz = 'Тз'

    number = '№ нап.'
    direction_type = 'Тип направления'
    traffic_lights = 'Светофоры'
    stages = 'Фазы, в кот. участ. направ.'
    always_red = 'Пост. красное'
    toov_green = 'Зелен.'
    toov_red = 'Красн.'
    description = 'Примечание'


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
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_green_ext): 0,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_flashing_green): 3,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_yellow): 3,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_red): 0,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_red_yellow): 1,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_z): 0,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_zz): 0,

    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_green_ext): 0,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_flashing_green): 3,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_yellow): 0,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_red): 3,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_red_yellow): 0,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_z): 0,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_zz): 0,

    (DirectionTypes.arrow, ColNamesDirectionsTable.t_green_ext): 0,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_flashing_green): 3,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_yellow): 0,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_red): 3,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_red_yellow): 0,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_z): 0,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_zz): 0,
}


if __name__ == '__main__':

    print(bool(DirectionTypes('Транспортно')))
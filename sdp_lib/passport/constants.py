from enum import StrEnum


class GroupTypes(StrEnum):
    common = 'Направление'
    vehicle = 'Транспортное'
    pedestrian = 'Пешеходное'
    arrow = 'Поворотное'
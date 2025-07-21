from collections.abc import MutableSequence
from dataclasses import dataclass, field, astuple

from sdp_lib.passport.constants import GroupTypes

data = '1\tТранспортное\t1,8,9\n2\tТранспортное\t1,2\n3\tТранспортное\t4\n4\tПоворотное\t2,3,4\n5\tТранспортное\t3,6,7,8,9,10\n6\tТранспортное\t5,6,7,10\n7\tТранспортное\t4,5,8,9\n8\tТранспортное\t1,2,3,4\n9\tПешеходное\t2,3\n10\tТранспортное\t1,5,6,7,8,9,10\n11\tПешеходное\t1,2,3,4,5,6,8,9\n12\tТранспортное\t2,3,4,5,6,7,10\n13\tТранспортное\t6,7,10\n14\tТранспортное\t1\n15\tПоворотное\t5,6,7,10\n16\tТранспортное\t5,6,7,8,9,10\n17\tТранспортное\t2,3,4\n18\tТранспортное\t7,10\n19\tТранспортное\t3,4,5,8,9,10\n20\tПешеходное\t3\n21\tТранспортное\t1,2,3,4\n22\tПешеходное\t1,2,3,4,5,8,9\n23\tТранспортное\t6,7\n24\tТранспортное\tПост.краси.\n'


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
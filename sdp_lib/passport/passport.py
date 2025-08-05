from collections.abc import MutableSequence, Sequence, MutableMapping

from sdp_lib.passport.directions import DirectionsTable
from sdp_lib.passport.time_programms import TimeProgramTable


class Passport:
    def __init__(
            self,
            *,
            directions_table: DirectionsTable | None,
            time_programs_tables: MutableMapping[int, TimeProgramTable] | None,
    ):
        self.directions_table = directions_table
        self.time_program_tables = time_programs_tables

    def __repr__(self):
        return (
            f'table_directions={self.directions_table}\n'
            f'table_stages={self.time_program_tables}'
        )

    def get_directions_table(self) -> DirectionsTable:
        return self.directions_table

    def get_time_program_tables(self) -> MutableMapping[int, TimeProgramTable]:
        return self.time_program_tables

    def load_directions_table(self, directions_table: DirectionsTable) -> bool:
        if isinstance(directions_table, DirectionsTable):
            self.directions_table = directions_table
            return True
        return False

    def load_time_program_table(self, stages_table: TimeProgramTable) -> bool:
        if isinstance(stages_table, TimeProgramTable):
            self.time_program_tables = stages_table
            return True
        return False


def build_passport(
    *,
    table_directions_data: str = None,
    table_stages_data: str = None
) -> Passport:
    directions_table = DirectionsTable(table_directions_data)
    time_program_tables = {}
    time_program1 = TimeProgramTable(table_stages_data)
    time_program_tables |= {1: time_program1}
    return Passport(directions_table=directions_table, time_programs_tables=time_program_tables)

if __name__ == '__main__':
    _data = '1\tТранспортное\t1,8,9\n2\tТранспортное\t1,2\n3\tТранспортное\t4\n4\tПоворотное\t2,3,4\n5\tТранспортное\t3,6,7,8,9,10\n6\tТранспортное\t5,6,7,10\n7\tТранспортное\t4,5,8,9\n8\tТранспортное\t1,2,3,4\n9\tПешеходное\t2,3\n10\tТранспортное\t1,5,6,7,8,9,10\n11\tПешеходное\t1,2,3,4,5,6,8,9\n12\tТранспортное\t2,3,4,5,6,7,10\n13\tТранспортное\t6,7,10\n14\tТранспортное\t1\n15\tПоворотное\t5,6,7,10\n16\tТранспортное\t5,6,7,8,9,10\n17\tТранспортное\t2,3,4\n18\tТранспортное\t7,10\n19\tТранспортное\t3,4,5,8,9,10\n20\tПешеходное\t3\n21\tТранспортное\t1,2,3,4\n22\tПешеходное\t1,2,3,4,5,8,9\n23\tТранспортное\t6,7\n24\tТранспортное\tПост.краси.\n'.rstrip()
    _data2 = '1\t1, 2, 8, 10, 11, 14, 21, 22\n2\t2, 4, 8, 9, 11, 12, 17, 22, 25\n3\t4, 5, 8, 9, 11, 12, 17, 19, 20, 21, 22\n4\t3, 4, 7, 8, 11, 12, 17, 19, 21, 22\n5\t6, 7, 10, 11, 12, 15, 16, 19, 22\n6\t5, 6, 10, 11, 12, 13, 15, 16, 23, 25\n7\t5, 6, 10, 12, 13, 15, 16, 18, 23, 25\n8\t1, 5, 7, 10, 11, 16, 19, 22\n9\t1, 5, 7, 10, 11, 16, 19, 22\n10\t5, 6, 10, 12, 13, 15, 16, 18, 19\n'.rstrip()
    passport1 = build_passport(table_directions_data=_data, table_stages_data=_data2)
    print(passport1.get_directions_table())

    print(passport1.get_directions_table().get_stages_data().get_direction_to_stages_mapping())
    print(passport1.get_directions_table().get_stages_data().get_stage_to_direction_mapping())
    print('*-*-*' * 100)
    print(passport1.get_time_program_tables()[1].get_stages_data().get_direction_to_stages_mapping())
    print(passport1.get_time_program_tables()[1].get_stages_data().get_stage_to_direction_mapping())




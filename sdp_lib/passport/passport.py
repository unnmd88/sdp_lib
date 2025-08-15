import pprint
from collections.abc import MutableSequence, Sequence, MutableMapping, Iterable

from sdp_lib.management_controllers.ssh.swarco_terminal import process_terminal_stdout
from sdp_lib.passport.base import StagesData, compare, compare_stages_data_for_directions_and_time_programs
from sdp_lib.passport.directions import DirectionsTable
from sdp_lib.passport.time_programms import TimeProgramTable, HeadDataRow
from sdp_lib.utils_common.utils_common import read_file_as_string


class Passport:
    def __init__(
            self,
            *,
            directions_data: str | DirectionsTable | None = None,
            time_programs_tables: Sequence[str] | None = None,
    ):
        if directions_data is None:
            self._directions_table = None
        elif isinstance(directions_data, str):
            self._directions_table = DirectionsTable(directions_data)
        elif isinstance(directions_data, DirectionsTable):
            self._directions_table = directions_data
        else:
            raise TypeError

        if time_programs_tables is None:
            self._time_program_tables = None
        elif isinstance(time_programs_tables, Sequence):
            self._time_program_tables = {
                num: TimeProgramTable(data, HeadDataRow(num)) for num, data in enumerate(time_programs_tables, 1)
            }
        else:
            raise TypeError

    def __repr__(self):
        return (
            f'table_directions={self._directions_table}\n'
            f'table_stages={self._time_program_tables}'
        )

    def get_directions_table(self) -> DirectionsTable:
        return self._directions_table

    def get_time_program_tables(self) -> MutableMapping[int, TimeProgramTable]:
        return self._time_program_tables

    def load_directions_table(self, directions_table: DirectionsTable) -> bool:
        if isinstance(directions_table, DirectionsTable):
            self._directions_table = directions_table
            return True
        return False

    def load_time_program_table(self, stages_table: TimeProgramTable) -> bool:
        if isinstance(stages_table, TimeProgramTable):
            self._time_program_tables = stages_table
            return True
        return False


if __name__ == '__main__':
    directions = DirectionsTable(read_file_as_string('directions_example').rstrip())
    stages = TimeProgramTable(read_file_as_string('time_program_example').rstrip())
    pprint.pprint(stages.get_stages_data())
    # print(
    #     compare_stages_data_for_directions_and_time_programs(
    #         directions.get_stages_data(),
    #         [(1, stages.get_stages_data())]
    #     )
    # )
    for comp_stages in compare_stages_data_for_directions_and_time_programs(directions.get_stages_data(),[(1, stages.get_stages_data())]):
        print(comp_stages)
        print(comp_stages.create_message().text)





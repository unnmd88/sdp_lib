from collections.abc import (
    Iterable,
    MutableMapping, Collection
)
from typing import NamedTuple

from sdp_lib.modbus.data_helpers import Description
from sdp_lib.modbus.fields import FieldNames
from sdp_lib.type_aliases import alias_matched_bit_states_to_descr, alias_matched_bit_addr_to_descr


# class Formatter:
#     def __init__(self, matched_val_to_description = None):
#         self._matched_bit_addr_to_description = {}
#         self.bind_bit_addr_to_description(matched_val_to_description)
#
#     def bind_bit_addr_to_description(
#             self,
#             state_to_val: Iterable[tuple[int, str]] | MutableMapping[int, str]
#     ):
#         if not state_to_val:
#             return
#         if isinstance(state_to_val, MutableMapping):
#             state_to_val = state_to_val.items()
#         for bit_addr, val in state_to_val:
#             self._matched_bit_addr_to_description[int(bit_addr)] = val
#
#     def get_bindings_bit_addr_to_val(self):
#         return self._matched_bit_addr_to_description
#
#     def states_as_pretty_string(self, states: list[bool]) -> str:
#         string_data = ''
#         for i, state in enumerate(states):
#             description = self._matched_bit_addr_to_description.get(i, "")
#             state_as_str = f'State={int(state)}'
#             string_data += f' <Bit address={i} {state_as_str}{description}>'
#         return string_data





class Formatter:
    def __init__(
            self,
            matched_bit_states_to_description: alias_matched_bit_states_to_descr,
            matched_bit_addr_to_description: alias_matched_bit_addr_to_descr
    ):
        self._matched_bit_states_to_description = matched_bit_states_to_description
        self._matched_bit_addr_to_description = matched_bit_addr_to_description

    # def create_data(self, states: list[bool]) -> PrettyStringAndStage:
    #     string_data = ''
    #     stage = -1
    #     for i, state in enumerate(states):
    #         try:
    #             if i not in self._matched_bit_addr_to_description[FieldNames.ignored_bits]:
    #                 d = self._matched_bit_addr_to_description[i]
    #                 description = d.string_pattern
    #                 stage = d.expected_val
    #             else:
    #                 description = ''
    #         except KeyError:
    #             description = ''
    #         state_as_str = f'State={int(state)}'
    #         string_data += f' <Bit address={i} {state_as_str}{description}>'
    #     return PrettyStringAndStage(string_data, stage)

    def create_data(self, states: list[bool]) -> str:
        string_data = ''
        for i, state in enumerate(states):
            try:
                d = self._matched_bit_addr_to_description[i]
                description = d.string_pattern
            except KeyError:
                description = ''
            state_as_str = f'State={int(state)}'
            string_data += f' <Bit address={i} {state_as_str}{description}>'
        return string_data

if __name__ == '__main__':
    ob = Formatter(
        {
            6: Description('(Stage=1)', 1),
            2: Description('(Stage=4)', 4),
            3: Description('(Stage=5)', 5),
            5: Description('(Stage=7)', 7)
        },
        {}
    )
    statees = [False, False, True, False, False, False, True, False]
    print(ob.create_data(statees))

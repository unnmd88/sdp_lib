from collections.abc import (
    Iterable,
    MutableMapping
)


class Formatter:
    def __init__(self, matched_val_to_description = None):
        self._matched_bit_addr_to_description = {}
        self.bind_bit_addr_to_description(matched_val_to_description)

    def bind_bit_addr_to_description(
            self,
            state_to_val: Iterable[tuple[int, str]] | MutableMapping[int, str]
    ):
        if not state_to_val:
            return
        if isinstance(state_to_val, MutableMapping):
            state_to_val = state_to_val.items()
        for bit_addr, val in state_to_val:
            self._matched_bit_addr_to_description[int(bit_addr)] = val

    def get_bindings_bit_addr_to_val(self):
        return self._matched_bit_addr_to_description

    def states_as_pretty_string(self, states: list[bool]) -> str:
        string_data = ''
        for i, state in enumerate(states):
            description = self._matched_bit_addr_to_description.get(i, "")
            state_as_str = f'State={int(state)}'
            string_data += f' <Bit address={i} {state_as_str}{description}>'
        return string_data



if __name__ == '__main__':
    ob = Formatter({6: '(Stage=1)', 2: '(Stage=4)', 3: '(Stage=5)', 5: '(Stage=7)'})
    print(ob.get_bindings_bit_addr_to_val())
    print(ob.states_as_pretty_string([False, False, True, False, False, False, True, False]))
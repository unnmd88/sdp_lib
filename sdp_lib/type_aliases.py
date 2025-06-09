from collections.abc import Iterable, MutableMapping
from typing import TypeAlias

from sdp_lib.modbus.data_helpers import Description

alias_matched_bit_states_to_descr: TypeAlias = (
    Iterable[Iterable[tuple[bool, ...], Description]] | MutableMapping[tuple[bool, ...], Description]
)
alias_matched_bit_addr_to_descr: TypeAlias = (
    Iterable[int, Description] | MutableMapping[int, Description]
)
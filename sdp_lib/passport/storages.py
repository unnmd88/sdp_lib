from dataclasses import dataclass, field
from typing import (
    Any,
    NamedTuple
)
from collections.abc import MutableSequence, Iterable, MutableMapping

from sdp_lib.passport.constants import MessageLevels, StorageNames


class Message(NamedTuple):
    text: str
    level: MessageLevels = MessageLevels.debug


def add_record(
    container: MutableSequence[Message] | MutableMapping[float, Any],
    records: Iterable[str | Message] | Iterable[tuple[float, Any]]
) -> int:
    cnt = 0
    if isinstance(container, MutableMapping):
        for key, row in records:
            cnt += 1
            container[key] = row
    elif isinstance(container, MutableSequence):
        for record in records:
            cnt += 1
            container.append(record)
    return cnt


@dataclass
class MessageStorage:
    name: str = ''
    errors: MutableSequence[Message] = field(default_factory=list)
    warnings: MutableSequence[Message] = field(default_factory=list)

    def set_name(self, name: str | StorageNames):
        self.name = name

    def add_errors(self, *errors: Message):
        return add_record(self.errors, errors)

    def add_warnings(self, *warnings: Message):
        return add_record(self.errors, warnings)


if __name__ == '__main__':
    msg = Message('Hello W!')
    msg_storage = MessageStorage()
    print(msg)

    print(msg_storage)
    msg_storage.add_errors(Message('This is number 2!'))
    print(msg_storage)
    print()

from collections.abc import MutableSequence
from typing import NamedTuple

from sdp_lib.passport.constants import MessageCategories
from sdp_lib.utils_common.utils_common import add_record


class Message(NamedTuple):
    text: str
    category: MessageCategories | int


class MessageStorage(NamedTuple):

    errors: MutableSequence[str | Message]
    warnings: MutableSequence[str | Message]

    def add_errors(self, *errors: Message):
        return add_record(self.errors, errors)

    def add_warnings(self, *warnings: Message):
        return add_record(self.warnings, warnings)

    def clear_all(self):
        self.errors.clear()
        self.warnings.clear()

    # def get_errors_by_categories(self, message_as_text=True):
    #     res = {}
    #     for msg in self.errors:
    #         m = msg.text if message_as_text else msg
    #         try:
    #             res[int(msg.category)][Fields.messages].append(m)
    #         except KeyError:
    #             cat, description = categories_descriptions.get(int(msg.category), (None, None))
    #             res[cat] = {
    #                 str(Fields.category_description): description,
    #                 str(Fields.messages): [m]
    #             }
    #     return res
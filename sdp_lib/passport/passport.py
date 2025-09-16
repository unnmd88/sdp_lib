from docx.document import Document

from sdp_lib.passport.base import TheTable


class Passport:
    def __init__(
            self,
            docx: Document,
            direction_table: TheTable = None,
    ):
        self._docx = docx
        self._direction_table = direction_table

    def get_docx(self):
        return self._docx

    def get_direction_table(self):
        return self._direction_table

    def load_direction_table(self, direction_table: TheTable):
        if not isinstance(direction_table, TheTable):
            raise TypeError(f'attr must be instance of {TheTable.__name__!r}. You give: {type(direction_table)}')
        self._direction_table = direction_table

    def dump(self):
        return {
            'tables': {
                'directions': self._direction_table.dump()
            }
        }
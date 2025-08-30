from collections.abc import MutableSequence
from pathlib import Path
from typing import IO

from docx.table import Table
from docx import Document

from sdp_lib.passport.passport2.doc_parsers.tables_sorting import sort


def parse_tables(tables: MutableSequence[Table]):
    pass


class DocTables:
    def __init__(self, tables: MutableSequence[Table]):

        self._directions = ...
        self._time_programs_ft = []
        self._time_programs_va = []

    def parse_tables(self, tables):
        pass

    def load_direction_table(self, table):
        self._directions = table

    def load_ft_time_program_tables(self, *tables):
        self._time_programs_ft += tables

    def load_va_time_program_tables(self, *tables):
        self._time_programs_va += tables


class Passport:
    def __init__(self, docx: str | Path | IO[bytes]):
        self._doc = Document(docx)
        self._tables_positions = sort(self._doc.tables)
        self._direction_table = ...


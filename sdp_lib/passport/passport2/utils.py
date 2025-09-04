from collections.abc import Iterable

from docx import Document
from docx.table import _Cell


def remove_left_light_spaces(cells: Iterable[_Cell]):
    return (s.text.rstrip().lstrip() for s in cells)


def _display_all_tables(doc_x):
    """ Выводит на экран данные всех таблиц doc(x) файла. """
    for table in doc_x.tables:
        print(f'-- Start Table --')
        print(f'Столбцов: {len(table.rows[0].cells)} | Строк: {len(table.rows)}')
        for i, row in enumerate(table.rows):
            print(f'{i}: {[cell.text for cell in row.cells]}')
        print(f'-- End Table --')
        print(f'*' * 100)


if __name__ == '__main__':
    path = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_'
    pattern = '/home/auser/Downloads/ПД Паспорт шаблон 2025'
    doc = Document(f'{pattern}.docx')
    _display_all_tables(doc)
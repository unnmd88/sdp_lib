import re
from collections.abc import Iterable, Container
from enum import Enum

from docx import Document
from docx.table import _Cell

from sdp_lib.passport.constants import Patterns


def remove_left_light_spaces_from_cells(cells: Iterable[_Cell]):
    return (s.text.rstrip().lstrip() for s in cells)


def remove_spaces_and_invalid_sep(string, sep=','):
    if (string:= string.replace(' ', '')) == '':
        return string
    # string = string.replace(' ', '')
    if sep == ',':
        string = re.sub(Patterns.more_than_one_comma.value, sep, string)
        return re.sub(Patterns.comma_is_start_end_or_spaces.value, '', string)
    string = re.sub(f'{sep}{sep}+', sep, string)
    return  re.sub(f'^{sep}|{sep}+$|.\s', '', string)




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
    path_sdp = "C:\Programms\py.projects\sdp_lib\sdp_lib\passport\СО_2094_ул_Островитянова_ул_Ак_Волгина (2)"
    doc = Document(f'{path_sdp}.docx')
    # _display_all_tables(doc)


    sepp = ','
    sepp2 = ';'
    strinnng1 = '   1,  ,2.3,  ,,,4,,,'
    strinnng2 = '1;;2.3;;4;'
    recovered = remove_spaces_and_invalid_sep(strinnng1, sepp)
    print(recovered)
    assert recovered == '1,2.3,4'

    recovered2 = remove_spaces_and_invalid_sep(strinnng2, sepp2)
    print(recovered2)
    assert recovered2 == '1;2.3;4'
    print(repr(remove_spaces_and_invalid_sep('', sepp2)))



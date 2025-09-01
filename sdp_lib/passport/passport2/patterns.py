import re
from collections.abc import Sequence
from enum import Enum



class Patterns(Enum):
    always_red = re.compile(r'кр|-|поко', re.IGNORECASE)


class DirectionTablePatterns(Enum):
    row1_cell0  = re.compile('^№\s*нап', re.IGNORECASE)
    row1_cell1  = re.compile('^тип\s*направления', re.IGNORECASE)
    row1_cell2  = re.compile('^фазы.*кот.*направ', re.IGNORECASE)
    row1_cell3  = re.compile('^светофоры', re.IGNORECASE)
    row1_cell4  = re.compile('^Тзд', re.IGNORECASE)
    row1_cell5  = re.compile('^Тзм', re.IGNORECASE)
    row1_cell6  = re.compile('^Тж', re.IGNORECASE)
    row1_cell7  = re.compile('^Тк', re.IGNORECASE)
    row1_cell8  = re.compile('^Ткж', re.IGNORECASE)
    row1_cell9  = re.compile('^Тз', re.IGNORECASE)
    row1_cell10 = re.compile('^Тзз', re.IGNORECASE)
    row1_cell11 = re.compile('^пост.+крас', re.IGNORECASE)
    row1_cell12 = re.compile('^Зел', re.IGNORECASE)
    row1_cell13 = re.compile('^Красн', re.IGNORECASE)
    row1_cell14 = re.compile('', re.IGNORECASE)

    @classmethod
    def get_patterns_len(cls, length: int):
        if length == 15:
            for pattern in cls:
                yield pattern.value
        elif length == 14:
            for i, pattern in enumerate(cls):
                if i != 10:
                    yield pattern.value


expected_template = ['№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Тз', 'Пост. красное', 'Зелен.', 'Красн.', '']


second_head_row15 = DirectionTablePatterns.get_patterns_len(15)
second_head_row14 = DirectionTablePatterns.get_patterns_len(14)

def match(row: Sequence[str]):
    for pattern, val in zip(second_head_row14, row, strict=True):
        if re.search(pattern, val) is None:
            print(f'val: {val}')
            yield val

if __name__ == '__main__':
    first_pattern = ['№ наeп.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Тз', 'Пост. красное', 'Зелен.', 'Красн.', '']


    res = [bad_el for bad_el in match(first_pattern)]
    print(res)
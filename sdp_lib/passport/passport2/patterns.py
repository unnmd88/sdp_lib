import re
from collections.abc import Sequence
from enum import Enum





#
# expected_template = ['№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Тз', 'Пост. красное', 'Зелен.', 'Красн.', '']
#
#
# second_head_row15 = DirectionTablePatterns.get_patterns_len(15)
# second_head_row14 = DirectionTablePatterns.get_patterns_len(14)
#
# def match(row: Sequence[str]):
#     for pattern, val in zip(second_head_row14, row, strict=True):
#         if re.search(pattern, val) is None:
#             print(f'val: {val}')
#             yield val
#
# if __name__ == '__main__':
#     first_pattern = ['№ наeп.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Тз', 'Пост. красное', 'Зелен.', 'Красн.', '']
#
#
#     res = [bad_el for bad_el in match(first_pattern)]
#     print(res)
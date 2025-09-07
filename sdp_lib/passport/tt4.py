import itertools
import re
from collections.abc import Iterable
from dataclasses import dataclass, asdict, fields, astuple
from enum import IntEnum
from typing import NamedTuple



def parse_tlc(direction, string: str, substrings: Iterable[str]):
    errors = []
    repaired_string = re.sub(',{2,}', ',', string)
    repaired_string = re.sub(',*$', '', repaired_string)

    first, *other = re.sub('\s*', '', repaired_string).split(',')
    if not (entity_tlc_is_valid:= any(re.match(sub_s, first, re.IGNORECASE) for sub_s in substrings)):
        errors.append('Неверный тип светофора для направления.')
    bad_nums = [bad_num for bad_num in other if not bad_num.isdigit()]
    if bad_nums:
        errors.append(f'Найдены некорректные номера светофоров: {bad_nums}')





    print(f'entity_tlc_is_valid: {entity_tlc_is_valid}')
    print(f'repaired_string: {repaired_string}')
    print(f'forst: {first}, other: {other}')
    print(f'bad_nums: {bad_nums}')
    print(f'errors: {errors}')



if __name__ == '__main__':
    parse_tlc('Транспортное', 'Тр. 13,15,,16g,', ['gр'])


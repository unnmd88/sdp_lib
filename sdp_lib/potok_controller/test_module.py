import re
import logging
import functools
import time
from rply import LexerGenerator
from typing import Dict

lg2 = LexerGenerator()

lg2.add("ddr", r'ddr\(D\d{1,3}\)')
lg2.add("ddo", r'ddo\(D\d{1,3}\)')
lg2.add("ngp", r'ngp\(D\d{1,3}\)')
# lg2.add("fctg", r'fctg\(G\d+\)\s+([<>]=?|==)(\d+)')
# lg2.add("fctg", r'fctg\(G\d+\)([<>]=?|==)\s+(\d+)')
# lg2.add("fctg", r'fctg\(G\d+\)\s+([<>]=?|==)\s+(\d+)')
# lg2.add("fctg", r'fctg\(G\d+\)([<>]=?|==)(\d+)')
lg2.add("fctg", r'fctg\(G\d+\)\s*([<>]=?|==)\s*(\d+)')
lg2.add('mr', r'\d+')

# lg2.ignore(r'[\s+\(\)]')
lg2.ignore(r'not|or|and|[\s+\(\)]')

string = "(ddr(D134) or ddr(D135) or ddr(D136) or not ddr(D137)) and (    fctg(G20) < 30)"
l = lg2.build()
for token in l.lex(string):
    print(token)
    print(token.value)

print([token.value.strip() for token in l.lex(string)])

start_time = time.time()



print(f'время составило: {time.time() - start_time}')



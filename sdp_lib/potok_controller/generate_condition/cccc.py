from collections import Counter
import re

l_parens = []
r_parens = []

expr = '((1|2)'
expr1 = '1|2'
e = ['((1|2) & 3)', '3|5 | 8-10']
cnt = Counter(expr)
print(cnt)
print(cnt['dddddd'])

print(any(c in '()' for c in expr))
print(any(c in '()' for c in expr1))

MATCHING_OPERATORS = {'|': 'or', '&': 'and', '-': 'or'}

p = f'[{"".join(MATCHING_OPERATORS)}]'
print(p)

rs = re.findall(r'(^\(+\)+)|(^\)+)', ')((()sadas)))')
exp = re.compile(r'\d+' + p + r'\d+')
exp1 = re.compile(r'\d+' + p + r'\d+' + f"|\d+")
exp2 = re.compile(p)
# rs = re.findall(r'\d+[]', ')((()sa2das)уке))')
# rs = re.findall(exp, ')((()sa2da2|3s)уке))')
rs = re.split(exp, '(9&))')
rs = re.split(exp, '()()(9&0))))PD19|12KS')
print(rs)
rs = re.findall(exp, ')()(14|15)(12|17')
print(rs)
rs = re.findall(exp2, '1|2')
print(f'rs: {rs}')
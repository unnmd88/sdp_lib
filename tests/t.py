# from sdp_lib.management_controllers.snmp import snmp_utils

from random import randint

l1 = [1, 2]

def get_random_scn():
    for x in range(10):
        if x == 7:
            print('yiels')
            yield x


l1 += get_random_scn()

print(l1)


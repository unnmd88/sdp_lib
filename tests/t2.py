# from sdp_lib.management_controllers import api

class Iter:

    def __iter__(self):
        return (x for x in range(10))

a = Iter()

print(list(a))
print(list(a))
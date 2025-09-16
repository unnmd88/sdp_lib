from sdp_lib.passport.constants import RowNames, TableNames


class ReprMixin:

    def __repr__(self):
        attrs = ' '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'{self.__class__.__name__}({attrs})'


class S(ReprMixin):
    __slots__ = ('_compare_stages', '_permission_to_set_flag_from_false_to_true')

    def __init__(self):
        self._compare_stages = True
        self._permission_to_set_flag_from_false_to_true = False

class D(ReprMixin):
    def __init__(self):
        self._x = 1
        self._y = 122


class EntityNameMixin:

    name: RowNames | TableNames



if __name__ == '__main__':
    s = S()
    d = D()
    print(s)
    print(d)


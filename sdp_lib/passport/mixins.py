


class ReprMixin:

    def __repr__(self):
        attrs = ' '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'{self.__class__.__name__}({attrs})'


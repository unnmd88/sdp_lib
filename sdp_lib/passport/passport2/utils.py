

def dump_as_dict(obj):
    try:
        return {attr: getattr(obj, attr) for attr in obj.__slots__}
    except AttributeError:
        return {k: v for k, v in obj.__dict__.items()}


def dump_as_tuple(obj):
    try:
        return ((attr, getattr(obj, attr)) for attr in obj.__slots__)
    except AttributeError:
        return (pair for pair in obj.__dict__.items())

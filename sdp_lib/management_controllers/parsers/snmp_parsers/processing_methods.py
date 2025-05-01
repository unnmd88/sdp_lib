from collections.abc import Callable


def get_val_as_str(val: int | str) -> str:
    return str(val)

def pretty_print(oid_or_val) -> str:
    print(f'тип oid_or_val: {oid_or_val}')
    return oid_or_val.prettyPrint()

def remove_chars(string, substring_to_remove) -> str:
    return str(string).replace(str(substring_to_remove), '')


def process_oid_with_replace_scn(scn: str):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            print(f'scn: {scn}')
            print(f'args: {args}, kwargs{kwargs}')
            oid = args[0]
            oid = remove_chars(oid, scn)
            return func(oid)
        return wrapper
    return decorator

def process_oid_with_replace_scn2(scn)



print(process_oid_with_replace_scn('10.12')(get_val_as_str)('1'))
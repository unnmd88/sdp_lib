from collections.abc import Callable


def get_val_as_str(val: int | str) -> str:
    return str(val)

def get_val_as_int(val: int | str) -> int | None:
    try:
        return int(val)
    except ValueError:
        return None

def pretty_print(oid_or_val) -> str:
    return oid_or_val.prettyPrint()

def remove_chars(string, substring_to_remove) -> str:
    return str(string).replace(str(substring_to_remove), '')

def build_func_with_remove_scn(scn: str, func: Callable) -> Callable:
    def wrapper_func(*args, **kwargs):
        oid_with_removed_scn = remove_chars(str(args[0]), scn)
        return func(oid_with_removed_scn)
    return wrapper_func






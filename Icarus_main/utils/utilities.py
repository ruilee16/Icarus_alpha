import regex as re
from os import walk
from typing import List


def update_dataclass(obj, **kwargs):
    for key, value in kwargs.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
        else:
            raise AttributeError(f"{type(obj).__name__} object has no attribute '{key}'")


def read_files_in_folder(fld: str, reg_exp: str = '.*?(.tif$)') -> List[str]:
    p = re.compile(reg_exp)
    _filenames = next(walk(fld), (None, None, []))
    return [f'{fld}\\{i}' for i in _filenames[-1] if p.match(i)]


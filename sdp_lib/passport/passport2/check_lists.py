from collections.abc import Container
from typing import NamedTuple, Any

from sdp_lib.passport.passport2.base2 import CellData, ValidationData


class TableGeometryCheckList(NamedTuple):
    allowed_col_lengths: Container
    allowed_min_num_rows: int
    num_columns: ValidationData
    num_rows: ValidationData


# class DirectionRowCheckList:
#     def __init__(
#             self,
#             number: CellData = None,
#             entity: CellData = None,
#             stages: CellData = None,
#             tlc: CellData = None,
#             t_green_ext: CellData = None,
#             t_green_flashing: CellData = None,
#             t_yellow: CellData = None,
#             t_red: CellData = None,
#             t_red_yellow: CellData = None,
#             t_z: CellData = None,
#             t_zz: CellData = None,
#             toov_green: CellData = None,
#             toov_red: CellData = None,
#             description: CellData = None,
#     ):
#         self.number = number
#         self.entity =  entity
#         self.stages = stages
#         self.tlc = tlc
#         self.t_green_ext = t_green_ext
#         self.t_green_flashing = t_green_flashing
#         self.t_yellow = t_yellow
#         self.t_red = t_red
#         self.t_red_yellow = t_red_yellow
#         self.t_z = t_z
#         self.t_zz = t_zz
#         self.toov_green = toov_green
#         self.toov_red = toov_red
#         self.description = description
#
#     def __setattr__(self, key, value):
#         if not isinstance(value, CellData):
#             raise ValueError(f'downloadable attr must be {CellData.__name__!r} instance.')
#         super().__setattr__(key, value)
#
#     def load_number(self, data: CellData):
#         if not isinstance(data, CellData):
#             raise ValueError(f'downloadable attr must be {CellData.__name__!r} instance.')
#         self.number = data
#
#     def load_entity(self, data: CellData):
#         if not isinstance(data, CellData):
#             raise ValueError(f'downloadable attr must be {CellData.__name__!r} instance.')
#         self.number = data


class DirectionRowCheckList:
    def __init__(self, row):
        pass

    def load_number(self, data: CellData):
        if not isinstance(data, CellData):
            raise ValueError(f'downloadable attr must be {CellData.__name__!r} instance.')
        self.number = data

    def load_entity(self, data: CellData):
        if not isinstance(data, CellData):
            raise ValueError(f'downloadable attr must be {CellData.__name__!r} instance.')
        self.number = data

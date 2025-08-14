# from dataclasses import (
#     dataclass,
#     field
# )
# from typing import (
#     Any,
#     NamedTuple,
#     TypeAlias
# )
# from collections.abc import (
#     MutableSequence,
#     Iterable,
#     MutableMapping
# )
#
# from sdp_lib.passport.constants import (
#     MessageLevels,
#     StorageNames,
#     StagesMapping,
#     RowNames,
#     TableNames
# )
#
#
# class Message(NamedTuple):
#     text: str
#     level: MessageLevels = MessageLevels.debug
#
#
# def add_record(
#     container: MutableSequence[Message] | MutableMapping[float, Any],
#     records: Iterable[str | Message] | Iterable[tuple[float, Any]]
# ) -> int:
#     cnt = 0
#     if isinstance(container, MutableMapping):
#         for key, row in records:
#             cnt += 1
#             container[key] = row
#     elif isinstance(container, MutableSequence):
#         for record in records:
#             cnt += 1
#             container.append(record)
#     return cnt
#
#
# @dataclass(slots=True)
# class MessageStorage:
#
#     name: str = ''
#     errors: MutableSequence[Message] = field(default_factory=list)
#     warnings: MutableSequence[Message] = field(default_factory=list)
#
#     def set_name(self, name: str | StorageNames):
#         self.name = name
#
#     def add_errors(self, *errors: Message):
#         return add_record(self.errors, errors)
#
#     def add_warnings(self, *warnings: Message):
#         return add_record(self.warnings, warnings)
#
#     def clear_all(self):
#         self.errors.clear()
#         self.warnings.clear()
#
#
# stages_content_type: TypeAlias = MutableMapping[float, set[float]]
#
#
# @dataclass
# class StagesData:
#     mapping_type: StagesMapping
#     _direction_to_stages_mapping: stages_content_type = field(default_factory=dict)
#     _stage_to_direction_mapping: stages_content_type = field(default_factory=dict)
#
#     def refresh(self, data: dict[float, set]):
#         if self.mapping_type == StagesMapping.direction_to_stages:
#             container1, container2 = self._direction_to_stages_mapping, self._stage_to_direction_mapping
#         elif self.mapping_type == StagesMapping.stage_to_direction:
#             container1, container2 = self._stage_to_direction_mapping, self._direction_to_stages_mapping
#         else:
#             raise TypeError(f'Invalid mapping_type: {self.mapping_type}')
#         if len(container1) > 0:
#             container1.clear()
#         container1 |= {k: v for k, v in data.items()}
#         if len(container2) > 0:
#             container2.clear()
#         for key, values in container1.items():
#             for value in values:
#                 try:
#                     container2[value].add(key)
#                 except KeyError:
#                     container2[value] = {key}
#
#     def get_direction_to_stages_mapping(self):
#         return self._direction_to_stages_mapping
#
#     def get_stage_to_direction_mapping(self):
#         return self._stage_to_direction_mapping
#
#     @property
#     def max_stage(self) -> int | float:
#         return max(self._stage_to_direction_mapping)
#
#     @property
#     def max_direction(self) -> int | float:
#         return max(self._direction_to_stages_mapping)
#
#
# compare_stages_entities = {RowNames.direction, RowNames.stage, TableNames.directions_table, TableNames.time_program}
#
#
# class Permissions:
#
#     __slots__ = ('_entity', '_compare_stages', '_permission_to_set_flag_from_false_to_true')
#
#     def __init__(self, entity: RowNames | TableNames = None):
#         self.initialize(entity)
#
#     def __repr__(self):
#         attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
#         return f'{self.__class__.__name__}({attrs})'
#
#     def initialize(self, entity: RowNames | TableNames):
#         self._entity = entity
#         self._compare_stages = True if entity in compare_stages_entities else False
#         self._permission_to_set_flag_from_false_to_true = False
#
#     def set_permission_set_flag_from_false_to_true(self, value: bool):
#         self._permission_to_set_flag_from_false_to_true = bool(value)
#
#     def _check_permission_and_return_flag(self, flag: bool):
#         flag = bool(flag)
#         if flag and self._permission_to_set_flag_from_false_to_true is False:
#             raise AttributeError("can't set attribute from False to True")
#         return flag
#
#     def set_val_for_compare_stages(self, flag: bool):
#         self._compare_stages = self._check_permission_and_return_flag(flag)
#
#     @property
#     def compare_stages(self) -> bool:
#         return self._compare_stages
#
#
# if __name__ == '__main__':
#     perm = Permissions()
#     print(perm)
#     print(perm.initialize(TableNames.directions_table))
#     print(perm)
#
#     perm2 = Permissions(TableNames.time_program)
#     print(perm2)
#
#
#     # act.set_val_for_compare_stages(False)
#     # act.set_permission_set_flag_from_false_to_true(True)
#     # act.set_val_for_compare_stages(True)
#     # print(act)

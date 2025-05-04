import abc
import typing
from collections.abc import Callable
from functools import cached_property

from sdp_lib.management_controllers.controller_modes import NamesMode
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.parser_core import Parsers
from sdp_lib.management_controllers.parsers.snmp_parsers.mixins import (
    StcipMixin,
    Ug405Mixin
)
from sdp_lib.management_controllers.parsers.snmp_parsers.processing_methods import (
    get_val_as_str,
    pretty_print
)
from sdp_lib.management_controllers.snmp.user_types import T_Varbinds
from sdp_lib.management_controllers.snmp.oids import Oids

from sdp_lib.management_controllers.snmp.snmp_utils import(
    StageConverterMixinPotokS,
    StageConverterMixinSwarco,
    StageConverterMixinUg405
)


class ConfigsParser(typing.NamedTuple):
    extras: bool
    oid_handler: Callable
    val_oid_handler: Callable
    host_protocol: str = None


default_processing = ConfigsParser(
    extras=False,
    oid_handler=get_val_as_str,
    val_oid_handler=pretty_print
)

pretty_processing_stcip = ConfigsParser(
    extras=True,
    oid_handler=get_val_as_str,
    val_oid_handler=pretty_print,
    host_protocol=FieldsNames.protocol_stcip
)

default_processing_ug405 = ConfigsParser(
    extras=False,
    oid_handler=get_val_as_str,
    val_oid_handler=pretty_print,
    host_protocol=FieldsNames.protocol_ug405
)


class BaseSnmpParser(Parsers):

    @property
    @abc.abstractmethod
    def matches(self) -> dict[str | Oids, tuple[FieldsNames, Callable]]:
        ...

    @property
    @abc.abstractmethod
    def extras_methods(self) -> dict[str, Callable]:
        ...

    def add_fields_to_response(self, **kwargs):
        for field_name, val in kwargs.items():
            self.parsed_content_as_dict[field_name] = val

    def add_host_protocol_to_response(self, protocol: str):
        self.add_fields_to_response(**{FieldsNames.host_protocol: protocol})

    def _add_extras_to_response(self):
        for field_name, cb_fn in self.extras_methods.items():
            self.parsed_content_as_dict[field_name] = cb_fn()

    def parse(
            self,
            *,
            varbinds: T_Varbinds,
            config: ConfigsParser = default_processing
    ):
        for oid, val in varbinds:
            oid, val = config.oid_handler(oid), config.val_oid_handler(val)
            print(f'oid: {oid} val: {val}')
            try:
                field_name, cb_fn = self.matches[oid]
                self.parsed_content_as_dict[field_name] = cb_fn(val)
            except TypeError:
                self.parsed_content_as_dict[oid] = val

        if config.extras:
            self._add_extras_to_response()

        self.add_host_protocol_to_response(config.host_protocol)
        self.data_for_response = self.parsed_content_as_dict
        return self.data_for_response


class ParsersVarbindsSwarco(BaseSnmpParser, StcipMixin):

    CENTRAL_PLAN              = '16'
    MANUAL_PLAN               = '15'
    SYNC_PLAN                 = '13'
    CONTROL_BLOCK_SOURCE      = '3'
    CALENDAR_CLOCK_SOURCE     = '7'
    TRAFFIC_SITUATION_SOURCE  = '6'
    FT_STATUS_TRUE            = '1'
    FT_STATUS_FALSE           = '0'

    host_protocol = FieldsNames.protocol_stcip

    def get_soft_flags_180_181_status(self, octet_string: str) -> str:
        return octet_string[179: 181]

    def get_current_mode(self) -> str | None:

        match (
            self.parsed_content_as_dict.get(FieldsNames.curr_plan),
            self.parsed_content_as_dict.get(FieldsNames.plan_source),
            self.parsed_content_as_dict.get(FieldsNames.fixed_time_status),
            self.parsed_content_as_dict.get(FieldsNames.status_soft_flag180_181, ''),
            int(self.parsed_content_as_dict.get(FieldsNames.num_detectors, '0'))

        ):
            case [self.CENTRAL_PLAN, self.CONTROL_BLOCK_SOURCE, *rest]:
                return str(NamesMode.CENTRAL)
            case [_, _, self.FT_STATUS_FALSE, '00', num_det] if num_det > 0:
                return str(NamesMode.VA)
            case [_, self.CALENDAR_CLOCK_SOURCE, fixed_status, flag180_181, num_det] if (
                '1' in flag180_181 or num_det == 0 or fixed_status == self.FT_STATUS_TRUE
            ):
                return str(NamesMode.FT)
            case[self.MANUAL_PLAN, self.CONTROL_BLOCK_SOURCE, *rest]:
                return str(NamesMode.MANUAL)
            case[self.SYNC_PLAN, source_plan, *rest] if source_plan in (
                self.CONTROL_BLOCK_SOURCE, self.TRAFFIC_SITUATION_SOURCE
            ):
                return str(NamesMode.SYNC)
        return None

    @property
    def extras_methods(self) -> dict[str, Callable]:
        return {FieldsNames.curr_mode: self.get_current_mode}

    @cached_property
    def matches(self):
        return {
            Oids.swarcoUTCTrafftechFixedTimeStatus: (FieldsNames.fixed_time_status, get_val_as_str),
            Oids.swarcoUTCTrafftechPlanSource: (FieldsNames.plan_source, get_val_as_str),
            Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, self.get_status),
            Oids.swarcoUTCTrafftechPhaseStatus:
                (FieldsNames.curr_stage, StageConverterMixinSwarco.get_num_stage_from_oid_val),
            Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, get_val_as_str),
            Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, get_val_as_str),
            Oids.swarcoSoftIOStatus: (FieldsNames.status_soft_flag180_181, self.get_soft_flags_180_181_status),
        }


class ParsersVarbindsPotokS(BaseSnmpParser, StcipMixin):

    modes = {
        '8': str(NamesMode.VA),
        '10': str(NamesMode.MANUAL),
        '11': str(NamesMode.CENTRAL),
        '12': str(NamesMode.FT),
    }

    def get_current_mode(self) -> str | None:
        return self.modes.get(
            self.parsed_content_as_dict.get(FieldsNames.curr_status_mode)
        )

    @property
    def extras_methods(self) -> dict[str, Callable]:
        return {FieldsNames.curr_mode: self.get_current_mode}

    @cached_property
    def matches(self):
        return {
        Oids.swarcoUTCStatusEquipment: (FieldsNames.curr_status, self.get_status),
        Oids.swarcoUTCTrafftechPhaseStatus:
            (FieldsNames.curr_stage, StageConverterMixinPotokS.get_num_stage_from_oid_val),
        Oids.swarcoUTCTrafftechPlanCurrent: (FieldsNames.curr_plan, get_val_as_str),
        Oids.swarcoUTCStatusMode: (FieldsNames.curr_status_mode, get_val_as_str),
        Oids.swarcoUTCDetectorQty: (FieldsNames.num_detectors, get_val_as_str),
    }


class ParsersVarbindsPotokP(BaseSnmpParser, Ug405Mixin):

    def get_current_mode(self) -> str | None:

        match (
            self.parsed_content_as_dict.get(FieldsNames.operation_mode),
            self.parsed_content_as_dict.get(FieldsNames.local_adaptive_status),
            self.parsed_content_as_dict.get(FieldsNames.num_detectors),
            self.parsed_content_as_dict.get(FieldsNames.has_det_faults),
            self.parsed_content_as_dict.get(FieldsNames.is_mode_man),
        ):
            case ['1', '1', num_det, '0', _] if num_det is not None and num_det.isdigit() and int(num_det) > 0:
                return str(NamesMode.VA)
            case ['1', '0', '0', _, _]:
                return str(NamesMode.FT)
            # case ['1', '0', num_det, '1', _] if num_det is not None and num_det.isdigit() and int(num_det) > 0:
            case ['1', '0', num_det, _, _] if num_det is not None and num_det.isdigit() and int(num_det) > 0:
                return str(NamesMode.FT)
            case [self.UTC_OPERATION_MODE, *rest]:
                return str(NamesMode.CENTRAL)
            case [*rest, '1']:
                return str(NamesMode.MANUAL)
        return None

    def get_current_status_mode(self) -> str | None:
        dark, flash = (
            self.parsed_content_as_dict.get(FieldsNames.dark),
            self.parsed_content_as_dict.get(FieldsNames.flash)
        )
        if dark == '0' and flash == '0':
            return str(FieldsNames.three_light)
        elif flash == '1':
            return str(FieldsNames.flash)
        elif dark == '1':
            return str(FieldsNames.dark)
        return None

    @property
    def extras_methods(self) -> dict[str, Callable]:
        return {
            FieldsNames.curr_status_mode: self.get_current_status_mode,
            FieldsNames.curr_mode: self.get_current_mode
        }

    @cached_property
    def matches(self):
        return {
            Oids.utcType2OperationMode: (FieldsNames.operation_mode, get_val_as_str),
            Oids.potokP_utcReplyDarkStatus: (FieldsNames.dark, get_val_as_str),
            Oids.utcReplyFR: (FieldsNames.flash, get_val_as_str),
            Oids.utcReplyGn: (FieldsNames.curr_stage, StageConverterMixinUg405.get_num_stage_from_oid_val),
            Oids.potokP_utcReplyPlanStatus: (FieldsNames.curr_plan, get_val_as_str),
            Oids.potokP_utcReplyLocalAdaptiv: (FieldsNames.local_adaptive_status, get_val_as_str),
            Oids.utcType2ScootDetectorCount: (FieldsNames.num_detectors,get_val_as_str),
            Oids.utcReplyDF: (FieldsNames.has_det_faults, get_val_as_str),
            Oids.utcReplyMC: (FieldsNames.is_mode_man, get_val_as_str),
        }


class ParsersVarbindsPeek(BaseSnmpParser, Ug405Mixin):
    @property
    def matches(self) -> dict[str | Oids, tuple[FieldsNames, Callable]]:
        return {}

    @property
    def extras_methods(self) -> dict[str, Callable]:
        return {}



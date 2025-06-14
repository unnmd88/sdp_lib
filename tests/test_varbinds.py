import logging
from random import randint
from contextlib import nullcontext as does_not_raise
import pytest

from sdp_lib.management_controllers.snmp.snmp_utils import *
from sdp_lib.management_controllers.snmp import oids

from sdp_lib import logging_config


logger = logging.getLogger(__name__)

ug405_set_stage_values = convert_val_to_num_stage_set_req_ug405(128)

swarco_stcip_varbinds = VarbSwarco()
potok_stcip_varbinds = VarbPotokS()
potok_ug405_varbinds = VarbPotokP()
peek_ug405_varbinds = VarbPeek()

vb_instances = (
swarco_stcip_varbinds,
potok_stcip_varbinds,
potok_ug405_varbinds,
peek_ug405_varbinds
)


def test_convert_val_to_num_stage_set_req_ug405():
    # stages = convert_val_to_num_stage_set_req_ug405(128)
    assert len(_ug405_set_stage_values) == 128
    assert _ug405_set_stage_values['1'] == '01'
    assert _ug405_set_stage_values['95'] == '400000000000000000000000'
    assert _ug405_set_stage_values['60'] == '0800000000000000'
    assert _ug405_set_stage_values['4'] == '08'

def test_wrap_oid_by_object_type():
    for oid in (o for o in oids.Oids):
        assert not isinstance(oid, ObjectType)
        obj = wrap_oid_by_object_type(oid)
        assert isinstance(obj, ObjectType)

@pytest.mark.parametrize(
    'scn_as_chars, converted_scn_as_chars_to_scn_as_ascii, expected',
    [
        ('CO1111', '.1.6.67.79.49.49.49.49', does_not_raise()),
        ('CO305', '.1.5.67.79.51.48.53', does_not_raise()),
        (1, '.1.5.67.79.51.48.53', pytest.raises(TypeError)),
        ([1], '.1.5.67.79.51.48.53', pytest.raises(TypeError)),
        (['abra'], '.1.5.67.79.51.48.53', pytest.raises(TypeError)),
        ({'1', 2}, '.1.5.67.79.51.48.53', pytest.raises(TypeError)),
    ]
)
def test_convert_chars_string_to_ascii_string(scn_as_chars, converted_scn_as_chars_to_scn_as_ascii, expected):
    with expected:
        assert convert_chars_string_to_ascii_string(scn_as_chars) == converted_scn_as_chars_to_scn_as_ascii

def get_random_scn() -> str:
    return convert_chars_string_to_ascii_string(f'CO{randint(1, 9999)}')

def get_stage_as_int_and_hex(num_stage=None) -> tuple[int, str]:
    num_stage = num_stage or randint(1, 129)
    val_stage = _ug405_set_stage_values.get(str(num_stage))
    stg_as_hex = OctetString(hexValue=val_stage).prettyPrint()
    return num_stage, stg_as_hex

def test_varbinds_instances():
    for inst in (swarco_stcip_varbinds, potok_stcip_varbinds):
        assert len(inst.get_varbinds_current_states()) > 4
    assert len(potok_ug405_varbinds.get_varbinds_current_states(get_random_scn())) > 4

def test_convert_val_as_hex_to_decimal():
    for num_stage in range(1, 129):
        _, stg_as_hex = get_stage_as_int_and_hex(num_stage)
        assert num_stage == convert_val_as_hex_to_decimal(stg_as_hex)



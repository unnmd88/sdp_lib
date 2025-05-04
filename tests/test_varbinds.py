import logging
from contextlib import nullcontext as does_not_raise
import pytest

from pysnmp.smi.rfc1902 import ObjectType

from sdp_lib.management_controllers.snmp import snmp_utils
from sdp_lib.management_controllers.snmp import oids

from sdp_lib import logging_config


logger = logging.getLogger(__name__)


def test_convert_val_to_num_stage_set_req_ug405():
    stages = snmp_utils.convert_val_to_num_stage_set_req_ug405(128)
    assert len(stages) == 128
    assert stages['1'] == '01'
    assert stages['95'] == '400000000000000000000000'
    assert stages['60'] == '0800000000000000'
    assert stages['4'] == '08'

def test_wrap_oid_by_object_type():
    for oid in (o for o in oids.Oids):
        assert not isinstance(oid, ObjectType)
        obj = snmp_utils.wrap_oid_by_object_type(oid)
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
        assert snmp_utils.convert_chars_string_to_ascii_string(scn_as_chars) == converted_scn_as_chars_to_scn_as_ascii





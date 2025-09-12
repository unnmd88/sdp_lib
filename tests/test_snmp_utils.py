import pickle

from sdp_lib.management_controllers.snmp import snmp_utils


def test_parse_varbinds_to_dict():
    expected = {
        '1.3.6.1.2.1.1.3.0': '3398636', '1.3.6.1.6.3.1.1.4.1.0': '1.3.6.1.4.1.1618',
        '1.3.6.1.4.1.1618.3.7.2.11.2.0': '2', '1.3.6.1.4.1.1618.3.5.2.1.6.1': '0x0d000b000b000b000b000c000a000a00'
    }
    with open('tests/vb.pkl' , 'rb') as f:
        assert snmp_utils.parse_varbinds_to_dict(pickle.load(f)) == expected

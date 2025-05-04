import pytest
from pysnmp.entity.engine import SnmpEngine

from sdp_lib.management_controllers.snmp import snmp_api


pytest_plugins = ('pytest_asyncio', )


@pytest.mark.asyncio
async def test_get_states_swarco():
    obj =  snmp_api.SwarcoStcip(ipv4='10.179.14.185', engine=SnmpEngine())
    await obj.get_states()
    # assert isinstance(obj.response_as_dict, abc.MutableMapping)
    for field in ['data', 'errors']:
        assert field in obj.response_as_dict




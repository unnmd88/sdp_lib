import pickle

import pytest

from sdp_lib.management_controllers.snmp import snmp_utils
from sdp_lib.management_controllers.snmp.trap_server.events import StageEvents


@pytest.fixture
def raw_varbinds(scope='module'):
    with open(f'vb.pkl', 'rb') as f:
        return snmp_utils.parse_varbinds_to_dict(pickle.load(f))

# ob = StageEvents(varbinds=vb, time_ticks=3398636, num_stage=1, val_stage='2', is_restart_cycle_stage_point=True, prev_event=None)
# ob1 = StageEvents(varbinds=vb, time_ticks=3498636, num_stage=2, val_stage='3', is_restart_cycle_stage_point=False, prev_event=ob)
# ob2 = StageEvents(varbinds=vb, time_ticks=3598636, num_stage=3, val_stage='4', is_restart_cycle_stage_point=False, prev_event=ob1)
# ob3 = StageEvents(varbinds=vb, time_ticks=3598736, num_stage=4, val_stage='4', is_restart_cycle_stage_point=True, prev_event=ob2)

@pytest.mark.usefixtures('raw_varbinds')
class TestStageEvents:
    @pytest.fixture
    def event1(self, raw_varbinds) -> StageEvents:
        return StageEvents(source='192.168.0.1', varbinds=raw_varbinds, time_ticks=3398636, num_stage=1, val_stage='2', is_restart_cycle_stage_point=True, prev_event=None)

    def test1(self, event1):
        assert isinstance(event1, StageEvents)
import pytest

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.snmp.trap_server.configparser import ConfigParser, NetworkInterface, CycleConfig, \
    Fields

# {'community': [['public', 'public'], ['UTMC', 'UTMC']],
#  'handlers': {'all_incoming_notifications': True,
#               'cycles': [['10.45.154.12', 'Поток (P)', 1, {'1': 2}]],
#               'stdout_incoming_notifications': True},
#  'network_interfaces': [['192.168.45.248', 164]],
#  'title': 'Trap receiver configuration'}
# {'community': [['public', 'public'], ['UTMC', 'UTMC']],
#  'handlers': {'all_incoming_notifications': True,
#               'cycles': [CycleConfig(ip='10.45.154.12', type_controller='Поток (P)', start_stage=1, prom_tacts={'1': 2})],
#               'stdout_incoming_notifications': True},
#  'network_interfaces': [NetworkInterface(ip='192.168.45.248', port=164)],
#  'title': 'Trap receiver configuration'}

config = ConfigParser("tests/tests_trap_server/config.toml")


class TestNetworkInterface:

    def test_valid_structure(self):
        instance = NetworkInterface('192.168.0.1', 162)
        assert instance.ip and instance.port


class TestConfigParser:

    # @pytest.fixture
    # def config(self) -> ConfigParser:
    #     return ConfigParser("config.toml")

    def test_valid_type_network_interfaces(self):
        """ Каждый элемент контейнера config.net_interfaces должен быть экземпляром класса CycleConfig."""
        assert all([isinstance(el, CycleConfig) for el in config.cycles])

    def test_valid_type_cycles(self):
        """ Каждый элемент контейнера config.cycles должен быть экземпляром класса NetworkInterface."""
        assert all([isinstance(el, NetworkInterface) for el in config.net_interfaces])

    def test_valid_community_struct(self):
        """ Каждый элемент контейнера config.net_interfaces должен быть контейнером из 2 объектов. """
        assert all([len(comm_pair) == 2 for comm_pair in config.net_interfaces])

    def test_get_handlers(self):
        handlers = {
            'all_incoming_notifications': True,
            'cycles': [CycleConfig(*['10.45.154.12', 'Поток (P)', 1, {}])],
            'stdout_incoming_notifications': True
        }
        assert config.get_handlers() == handlers

    def test_net_interfaces_property(self):
        net_interface = [NetworkInterface('192.168.45.248', 164)]
        assert config.net_interfaces == net_interface

    def test_community_property(self):
        communities = [['public', 'public'], ['UTMC', 'UTMC']]
        assert config.community == communities

    def test_has_has_handlers_property(self):
        assert config.has_handlers

    def test_has_cycles_property(self):
        assert config.has_cycles

    def test_all_incoming_notifications_property(self):
        assert config.all_incoming_notifications

    def test_stdout_incoming_notifications_property(self):
        assert config.stdout_incoming_notifications
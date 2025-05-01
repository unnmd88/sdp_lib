import os
import typing

from dotenv import load_dotenv

from sdp_lib.management_controllers.fields_names import FieldsNames


load_dotenv()


class HostSnmpConfig(typing.NamedTuple):
    """ Конфигурация snmp протокола """

    community_r: str
    community_w: str
    name_protocol: str
    has_scn_dependency: bool


stcip = HostSnmpConfig(
    community_r=os.getenv('communitySTCIP_r'),
    community_w=os.getenv('communitySTCIP_r'),
    name_protocol=FieldsNames.protocol_stcip,
    has_scn_dependency=False
)

ug405 = HostSnmpConfig(
    community_r=os.getenv('communityUG405_r'),
    community_w=os.getenv('communityUG405_w'),
    name_protocol=FieldsNames.protocol_ug405,
    has_scn_dependency=True
)

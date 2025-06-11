from sdp_lib.management_controllers.exceptions import BadControllerType
from sdp_lib.management_controllers.structures import SnmpResponseStructure

# Deprecated
class ErrorResponseCheckers:

    def __init__(self, host_instance):
        self.host_instance = host_instance

    def check_response_errors_and_add_to_host_data_if_has(self):
        """
            self.__response[ResponseStructure.ERROR_INDICATION] = error_indication: errind.ErrorIndication,
            self.__response[ResponseStructure.ERROR_STATUS] = error_status: Integer32 | int,
            self.__response[ResponseStructure.ERROR_INDEX] = error_index: Integer32 | int
        """
        if self.host_instance._tmp_response[SnmpResponseStructure.ERROR_INDICATION] is not None:
            self.host_instance.add_data_to_data_response_attrs(self.host_instance._tmp_response[SnmpResponseStructure.ERROR_INDICATION])
        elif (
            self.host_instance._tmp_response[SnmpResponseStructure.ERROR_STATUS]
            or self.host_instance._tmp_response[SnmpResponseStructure.ERROR_INDEX]
        ):
            self.host_instance.add_data_to_data_response_attrs(BadControllerType())
        return bool(self.host_instance.response_errors)
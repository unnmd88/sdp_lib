from sdp_lib.management_controllers.http.peek import routes
from sdp_lib.management_controllers.http.peek.monitoring.monitoring_core import GetData
from sdp_lib.management_controllers.parsers.parsers_peek_http import MainPageParser


class MainPage(GetData):

    route = routes.main_page
    parser_class = MainPageParser
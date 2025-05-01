import os

from dotenv import load_dotenv


load_dotenv()

main_page =  os.getenv('ROUTE_GET_CURRENT_STATE')
get_inputs = os.getenv('ROUTE_GET_INPUTS')
set_inputs = os.getenv('ROUTE_SET_INPUTS')
get_user_params = os.getenv('ROUTE_GET_USER_PARAMETERS')
set_user_params = os.getenv('ROUTE_SET_USER_PARAMETERS')
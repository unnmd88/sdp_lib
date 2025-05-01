from enum import StrEnum


class FieldsNames(StrEnum):

    ipv4_address = "ip_address"
    errors = 'errors'
    entity = 'entity'
    data = 'data'
    response = 'response'

    host_protocol = 'host_protocol'
    protocol = 'protocol'
    protocol_snmp = 'snmp'
    protocol_stcip = 'stcip'
    protocol_ug405 = 'ug405'
    protocol_utmc = 'utmc'
    protocol_http = 'http'
    protocol_ssh = 'ssh'
    web_content = 'web_content'
    source = 'source'

    num_streams = 'number_of_streams'
    streams_data = 'streams_data'
    curr_xp = 'xp'
    curr_address = 'current_address'
    curr_stage = 'current_stage'
    num_detectors = 'num_detectors'
    has_det_faults = 'has_det_faults'
    status_soft_flag180_181 = 'status_soft_flag180_181'
    curr_plan = 'current_plan'
    curr_time = 'current_time'
    curr_plan_param = 'current_plan_parameter'
    curr_alarms = 'current_alarms'
    curr_mode = 'current_mode'
    curr_status = 'current_status'
    curr_state = 'current_state'
    curr_status_mode = 'curr_status_mode'
    plan_source = 'plan_source'
    fixed_time_status = 'fixed_time_status'
    local_adaptive_status = 'local_adaptive_status'
    is_mode_man = 'is_mode_man'
    inputs = 'inputs'
    sent_data = 'sent_data'

    bit_TO = 'TO_bit'
    operation_mode = 'operation_mode'

    power_up = 'powerUp'
    dark = 'dark'
    flash = 'flash'
    three_light = '3_light'
    all_red = 'all_red'

    red_yellow_green = 'red_yellow_green'

    #Set command section
    set_stage = 'set_stage'



class ErrorMessages(StrEnum):
    bad_controller_type = 'bad_controller_type'


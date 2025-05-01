import os

first_man_inp: int = int(os.getenv('first_man_inp'))
man_inp = first_man_inp + 1
first_inp_stage = first_man_inp + 3
last_inp_stage = int(os.getenv('last_inp_stage'))
first_hardw_inp = os.getenv('start_hardw_input')
flash_enable = os.getenv('flash_enable')
flash_disable = os.getenv('flash_disable')
signals_on = os.getenv('signals_on')
signals_off = os.getenv('signals_off')
btn_local_enable = os.getenv('btn_local_enable')
btn_local_disable = os.getenv('btn_local_disable')
stdout_encoding = os.getenv('stdout_encoding')
stdout_decoding = os.getenv('stdout_decoding')
term_type = os.getenv('term_type')
proc_ssh_encoding = os.getenv('proc_ssh_encoding')
user_itc = os.getenv('user_itc')
inputs_curr_state = os.getenv('inputs_curr_state')
inps_ = os.getenv('hardw_inp')

kex_algs = os.getenv('kex_algs')
enc_algs = os.getenv('enc_algs')

itc_login = os.getenv('swarco_itc_login')
itc_passwd = os.getenv('swarco_itc_passwd')
swarco_r_login = os.getenv('swarco_r_login')
swarco_r_passwd = os.getenv('swarco_r_passwd')
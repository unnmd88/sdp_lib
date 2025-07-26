import re

from sdp_lib.passport.base import AbstractEntity


class Program(AbstractEntity):

    TIME_INTERVAL_PATTERN = re.compile('\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}')

    def __init__(
            self,
            num_stage: str,
            directions: str,
            num: str = '',
            t_cyc: str = '',
            weekdays: str = '',
            time_interval = '',
            t_osn: str = '',
            t_sdvig: str = '',
            t_min_man: str = '',
            t_min_va: str = '',
            t_max1_va: str = '',
            t_max2_va: str = '',
            req_condition: str = '',
            ext_condition: str = '',
            term_condition: str = ''

    ):
        super().__init__()
        self._is_full = False
        self.num_stage = num_stage
        self.directions = directions
        self.num = num
        self.t_cyc = t_cyc
        self.weekdays = weekdays
        self.time_interval = re.findall(self.TIME_INTERVAL_PATTERN, time_interval)
        self.t_osn = t_osn
        self.t_sdvig = t_sdvig
        self.t_min_man = t_min_man
        self.t_min_va = t_min_va
        self.t_max1_va = t_max1_va
        self.t_max2_va = t_max2_va
        self.req_condition = req_condition
        self.ext_condition = ext_condition
        self.term_condition = term_condition

    def _extra_init_and_check_data(self):
        pass




if __name__ == '__main__':
    r = re.compile('\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}')
    print(re.findall(r, '07:00:00-11:00:00'))
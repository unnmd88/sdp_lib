from sdp_lib.management_controllers import api

obj3 = api.PotokS(ipv4='10.179.65.153')

res = obj3.varbinds.get_num_stage_from_oid_val('9')
print(res)
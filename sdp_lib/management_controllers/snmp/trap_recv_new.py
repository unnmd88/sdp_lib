from pysnmp.entity import engine, config
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv

# Create SNMP engine with autogenernated engineID and pre-bound
# to socket transport dispatcher
snmpEngine = engine.SnmpEngine()

# Transport setup

# UDP over IPv4, first listening interface/port
config.add_transport(
    snmpEngine,
    udp.DOMAIN_NAME + (1,),
    udp.UdpTransport().open_server_mode(("192.168.45.248", 164)),
)

# UDP over IPv4, second listening interface/port
# config.add_transport(
#     snmpEngine,
#     udp.DOMAIN_NAME + (2,),
#     udp.UdpTransport().open_server_mode(("127.0.0.1", 2162)),
# )

# SNMPv1/2c setup

# SecurityName <-> CommunityName mapping
config.add_v1_system(snmpEngine, "my-area", "public")


# Callback function for receiving notifications
# noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
def cbFun(snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):
    print(
        'Notification from ContextEngineId "{}", ContextName "{}"'.format(
            contextEngineId.prettyPrint(), contextName.prettyPrint()
        )
    )
    for name, val in varBinds:
        print(f"{name.prettyPrint()} = {val.prettyPrint()}")


# Register SNMP Application at the SNMP engine
ntfrcv.NotificationReceiver(snmpEngine, cbFun)

snmpEngine.transport_dispatcher.job_started(1)  # this job would never finish

# Run I/O dispatcher which would receive queries and send confirmations
try:
    snmpEngine.open_dispatcher()
except:
    snmpEngine.close_dispatcher()
    raise
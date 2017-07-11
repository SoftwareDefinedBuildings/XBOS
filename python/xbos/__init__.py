from bw2python.client import Client as BW2Client
import os

__all__ = ['devices','services','util']

def get_client(agent=None,entity=None):
    # set defaults
    if agent is None:
        agent = os.environ.get('BW2_AGENT','127.0.0.1:28589')
    if entity is None:
        entity = os.environ.get('BW2_DEFAULT_ENTITY',None)

    if agent is None:
        raise Exception("Need to provide an agent or set BW2_AGENT")
    if entity is None:
        raise Exception("Need to provide an entity or set BW2_DEFAULT_ENTITY")

    hostname, port = agent.split(':')
    c = BW2Client(hostname, int(port))
    c.setEntityFromFile(entity)
    c.overrideAutoChainTo(True)

    return c

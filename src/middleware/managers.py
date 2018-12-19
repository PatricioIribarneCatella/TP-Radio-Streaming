import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import middleware.constants as cons
import rebroadcast.messages as m
from middleware.channels import InterNode, InterProcess, Poller

class LeaderElection(object):

    def __init__(self, country, nodes, aid, config):
        
        self.country = country
        self.nodes = nodes
        self.config = config
        self.aid = aid

        self.anthena = InterNode(cons.PUSH)

        self.monitorc = InterProcess(cons.PUSH)
        self.monitorc.bind("monitor-{}-{}".format(country, aid))

        fd = InterProcess(cons.PULL)
        fd.bind("fail-{}-{}".format(country, aid))
        
        le = InterNode(cons.PULL)
        le.bind(config["anthena"][country][str(self.aid)]["bind"])

        self.poller = Poller([fd, le])

    def monitor(self, message):

        self.monitorc.send(message)

    def send(self, message, receivers, node_type):

        interface = None

        for rid in receivers:
            self.anthena.disconnect(interface)
            interface = self.config[node_type][self.country][str(rid)]["connect"]
            self.anthena.connect(interface)
            self.anthena.send(message)

    def recv(self):

        socks = self.poller.poll(None)

        for s, poll_type in socks:
            if poll_type == cons.POLLIN:
                msg, nid = s.recv()
                #print("node: {} - recv msg: {}, nid: {}".format(self.aid, msg, nid))
                yield msg, nid




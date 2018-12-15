import sys
import time
from os import path
from multiprocessing import Process

import zmq

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from middleware.channels import InterProcess, InterNode, TimeOut
import middleware.constants as cons
import rebroadcast.messages as m

class Detector(Process):

    def __init__(self, country, nodeid, config):

        self.aid = nodeid
        self.country = country
        self.config = config

        super(Detector, self).__init__()

    def _initialize(self):

        self.monitor = InterProcess(cons.PULL)
        self.monitor.connect("monitor-{}-{}".format(
                        self.country, self.aid))

        self.fail = InterProcess(cons.PUSH)
        self.fail.connect("fail-{}-{}".format(
                        self.country, self.aid))
        
        self.next = InterNode(cons.REQ)

    def _monitor_node(self):

        # Receives id of the node
        # to be monitored
        mtype, nid = self.monitor.recv()
        print("mtype: {}".format(mtype))

        # If the message type is "CLEAR"
        # it means the node is the 'Leader'
        # and it does not need to monitor any node
        while mtype == m.CLEAR_MONITOR:
            mtype, nid = self.monitor.recv()
            print("mtype: {}".format(mtype))
        
        print("hola")
        self.next.connect(config["anthena"][self.country][str(nid)]["connect"],
                          timeout=1)

    def run(self):

        # Initialize detector´s connections
        self._initialize()

        print("Failure detector running. Country: {}, id: {}".format(
                    self.country, self.aid))

        self._monitor_node()
        
        while True:

            self.next.send({"mtype": m.IS_ALIVE,
                            "node": self.aid})

            try:
                msg, nid = self.next.recv()
            except TimeOut:
                self.fail.send({"mtype": m.FAIL, "node": 0})
                self._monitor_node()
            
            # Simulate time passed
            time.sleep(1)

        self.node.close()
        self.next.close()

        print("Failure detector from {} and id:{} down".format(
                self.country, self.aid))



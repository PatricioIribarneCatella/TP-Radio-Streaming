import os
import sys
import signal
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import rebroadcast.messages as m
from middleware.managers import LeaderElection
from rebroadcast.failure import Detector
from rebroadcast.heartbeat import HeartbeatSender
from rebroadcast.states import Leader, Normal

class LeaderCoordinator(object):

    def __init__(self, country, nodes, aid, config):

        self.country = country
        self.nodes = nodes
        self.config = config
        self.aid = aid
        self.quit = False

        self.connection = LeaderElection(self.country,
                                         self.nodes,
                                         self.aid,
                                         self.config)

        self.handlers = {
            m.ALIVE: self._react_on_alive,
            m.FAIL: self._react_on_fail,
            m.IS_LEADER: self._react_on_leader_question
        }

    def _sig_handler(self, signum, frame):
        self.quit = True

    def _lesser(self):

        return [i for i in range(1, self.aid)]

    def _react_on_alive(self, nid):

        print("node: {} recv ALIVE from {}".format(self.aid, nid))

        if (self.next == None) or (self.next > nid):
            
            self.connection.monitor({"mtype": m.START_MONITOR, "node": nid})
            
            if self.next == None:
                self.state = Normal()
                print("node: {} is NORMAL".format(self.aid))

            self.next = nid

    def _react_on_fail(self, nid):

        print("node: {} recv FAIL from {}".format(self.aid, nid))

        nid += 1

        if nid > self.nodes:
            # This node is the leader
            self.state = Leader()
            self.connection.monitor({"mtype": m.CLEAR_MONITOR, "node": 0})
            self.next = None
            print("node: {} is LEADER".format(self.aid))
        else:
            # Starts monitoring next node
            self.connection.monitor({"mtype": m.START_MONITOR, "node": nid})
            self.next = nid
            print("node: {} continue being NORMAL".format(self.aid))

    def _react_on_leader_question(self, nid):

        print("node: {} recv LEADER? from {}".format(self.aid, nid))

        mtype = m.LEADER if self.state.leader() else m.NOT_LEADER

        self.connection.send({"mtype": mtype, "node": self.aid},
                                 [nid], "station")

    def _recovery(self):

        # Notifies nodes with smaller priority that its alive
        self.connection.send({"mtype": m.ALIVE, "node": self.aid},
                                self._lesser(), "anthena")

        nextid = self.aid + 1

        if nextid > self.nodes:
            # This node is the leader
            self.state = Leader()
            self.connection.monitor({"mtype": m.CLEAR_MONITOR, "node": 0})
            self.next = None
            print("node: {} is LEADER".format(self.aid))
        else:
            # Starts monitoring the next node
            self.connection.monitor({"mtype": m.START_MONITOR, "node": nextid})
            self.next = nextid
            self.state = Normal()
            print("node: {} is NORMAL".format(self.aid))

    def _loop(self):

        for msg, nid in self.connection.recv():

            handler = self.handlers.get(msg)

            handler(nid)

    def run(self):

        print("Leader module running. Country: {}, id: {}".format(
                    self.country, self.aid))

        d = Detector(self.country, self.aid, self.config)
        d.start()

        hb = HeartbeatSender(self.country, self.aid, self.config)
        hb.start()

        # Save pids to stop them after
        with open("pids-{}-{}.store".format(self.country, self.aid), "a") as f:
            f.write(str(d.pid) + "\n")
            f.write(str(hb.pid) + "\n")

        # Set signal handler
        signal.signal(signal.SIGINT, self._sig_handler)

        self._recovery()

        while not self.quit:
            self._loop()

        os.kill(d.pid, signal.SIGINT)
        os.kill(hb.pid, signal.SIGINT)

        d.join()
        hb.join()

        print("Leader module down")



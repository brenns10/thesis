#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""Mininet detour experiment.

This script contains several important items. First, it contains a class
declaring my experimental network topology. Second, a function that defines
routes and anything else required to make this topology work. You can see a
diagram of the topology below:

    client --- r1 ---------------------- r2 --- server
                \                        /
                 ---------  r3  ---------
                            |
                          detour

Finally, this script contains my experiment and data collection mechanisms.
Simply put, for each set of experimental parameters, we create a Mininet, start
all necessary detour and client processes, and then run iperf several times.
Throughput statistics are saved, and for at least one iteration, a tcpdump
containing only headers is created for future inspection.

"""
from __future__ import print_function

import os
import sys

from mininet.cli import CLI
from mininet.log import lg, LEVELS
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.util import waitListening


BASIC_PARAMS = {
    'client_r1': {'delay': '5ms', 'bw': 20},
    'r1_r2': {'delay': '5ms', 'bw': 10},
    'r2_server': {'delay': '5ms', 'bw': 20},
    'r1_r3': {'delay': '5ms', 'bw': 20},
    'r2_r3': {'delay': '5ms', 'bw': 20},
    'r3_detour': {'delay': '5ms', 'bw': 20},
}


class DetourTopo(Topo):
    "Simple topology example."

    def __init__(self, params):
        "Create custom topo."

        # Initialize topology
        Topo.__init__(self)

        # Add hosts and switches
        client = self.addHost('client')
        r1 = self.addHost('r1')
        r2 = self.addHost('r2')
        server = self.addHost('server')
        r3 = self.addHost('r3')
        detour = self.addHost('detour')

        # Add links
        self.addLink(client, r1, **params.get('client_r1', {}))
        self.addLink(r1, r2, **params.get('r1_r2', {}))
        self.addLink(r2, server, **params.get('r2_server', {}))
        self.addLink(r1, r3, **params.get('r1_r3', {}))
        self.addLink(r2, r3, **params.get('r2_r3', {}))
        self.addLink(r3, detour, **params.get('r3_detour', {}))


topos = {'detour': DetourTopo}


def clear_routes(*nodes):
    for node in nodes:
        node.cmd('ip route flush table main')


def DetourNet(params):
    """A function that looks like a class... ಠ_ಠ.

    This function returns a *started* mininet instance, containing the detour
    topology, fully initialized with all IP addresses and routing tables.
    """
    topo = DetourTopo(params)
    mn = Mininet(topo=topo, link=TCLink)
    mn.start()
    client, server, detour = mn.get('client', 'server', 'detour')
    r1, r2, r3 = mn.get('r1', 'r2', 'r3')

    ### SET IP ADDRESSES (by subnet)
    # 10.0.1.0/24
    client.connectionsTo(r1)[0][0].setIP('10.0.1.1/32')
    r1.connectionsTo(client)[0][0].setIP('10.0.1.2/32')
    # 10.0.2.0/24
    r1.connectionsTo(r2)[0][0].setIP('10.0.2.1/32')
    r2.connectionsTo(r1)[0][0].setIP('10.0.2.2/32')
    # 10.0.3.0/24
    r2.connectionsTo(server)[0][0].setIP('10.0.3.1/32')
    server.connectionsTo(r2)[0][0].setIP('10.0.3.2/32')
    # 10.0.4.0/24
    r1.connectionsTo(r3)[0][0].setIP('10.0.4.1/32')
    r3.connectionsTo(r1)[0][0].setIP('10.0.4.2/32')
    # 10.0.5.0/24
    r2.connectionsTo(r3)[0][0].setIP('10.0.5.1/32')
    r3.connectionsTo(r2)[0][0].setIP('10.0.5.2/32')
    # 10.0.6.0/24
    r3.connectionsTo(detour)[0][0].setIP('10.0.6.1/32')
    detour.connectionsTo(r3)[0][0].setIP('10.0.6.2/32')

    ### SET ROUTING TABLES
    clear_routes(client, server, detour, r1, r2, r3)
    # The client, detour, and server routes are easy, since they're thru a gw
    client.setHostRoute('10.0.1.2', client.defaultIntf())
    client.cmd('route add -net 10.0.0.0/8 gw 10.0.1.2')
    detour.setHostRoute('10.0.6.1', detour.defaultIntf())
    detour.cmd('route add -net 10.0.0.0/8 gw 10.0.6.1')
    server.setHostRoute('10.0.3.1', server.defaultIntf())
    server.cmd('route add -net 10.0.0.0/8 gw 10.0.3.1')
    # r1 routes most traffic thru r2, except the 10.0.6.0/24 subnet
    r1.setHostRoute('10.0.1.1', r1.connectionsTo(client)[0][0])
    r1.setHostRoute('10.0.4.2', r1.connectionsTo(r3)[0][0])
    r1.setHostRoute('10.0.2.2', r1.connectionsTo(r2)[0][0])
    r1.cmd('route add -net 10.0.6.0/24 gw 10.0.4.2') # thru r3
    r1.cmd('route add -net 10.0.0.0/8 gw 10.0.2.2')  # thru r2
    # r2 routes most traffic thru r1, except the 10.0.6.0/24 subnet
    r2.setHostRoute('10.0.2.1', r2.connectionsTo(r1)[0][0])
    r2.setHostRoute('10.0.5.2', r2.connectionsTo(r3)[0][0])
    r2.setHostRoute('10.0.3.2', r2.connectionsTo(server)[0][0])
    r2.cmd('route add -net 10.0.6.0/24 gw 10.0.5.2') # thru r3
    r2.cmd('route add -net 10.0.0.0/8 gw 10.0.2.1')  # thru r1
    # r3 routes most traffic thru r2, except the 10.0.1.0/24 subnet
    r3.setHostRoute('10.0.6.2', r3.connectionsTo(detour)[0][0])
    r3.setHostRoute('10.0.5.1', r3.connectionsTo(r2)[0][0])
    r3.setHostRoute('10.0.4.1', r3.connectionsTo(r1)[0][0])
    r3.cmd('route add -net 10.0.1.0/24 gw 10.0.4.1') # thru r1
    r3.cmd('route add -net 10.0.0.0/8 gw 10.0.5.1')  # thru r2

    ### ENABLE PACKET FORWARDING
    r1.cmd('sysctl -w net.ipv4.ip_forward=1')
    r2.cmd('sysctl -w net.ipv4.ip_forward=1')
    r3.cmd('sysctl -w net.ipv4.ip_forward=1')

    return mn


def setup_nat(client, detour):
    client.cmd('./client daemon ../etc/daemon-nat-vm.conf')
    detour.cmd('python nat_detour.py &')


def setup_vpn(client, detour):
    client.cmd('./client daemon ../etc/daemon-vpn-vm.conf')
    detour.cmd('./vpn_detour.sh &')


def setup_ctrl(client, detour):
    pass


SETUP = {
    'nat': setup_nat,
    'vpn': setup_vpn,
    'control': setup_ctrl,
}


def scenario(name, params, trials=30):
    mn = DetourNet(params)
    client, detour, server = mn.get('client', 'detour', 'server')
    SETUP[params['scenario']](client, detour)

    filename = '%s.%s.csv' % (name, params['scenario'])
    server.sendCmd('iperf -s -y c | tee %s' % filename)

    # sleep synchronization is the worst, except for iperf
    import time; time.sleep(0.5)

    for _ in range(trials):
        print('.', end='')
        sys.stdout.flush()
        client.cmd('iperf -c ' + server.IP() + ' -y c')
        server.monitor()     # ensure a line of server output was created
    print()

    mn.stop()


def easy():
    for name in SETUP:
        print('Scenario %s: ' % name, end='')
        params = {'scenario': name}
        params.update(BASIC_PARAMS)
        scenario('easy', params)
    os.system('dmesg > dmesg.easy.log')


def lossy():
    for name in SETUP:
        print('Scenario %s: ' % name, end='')
        params = {'scenario': name}
        params.update(BASIC_PARAMS)
        params['r1_r2']['loss'] = 1
        scenario('lossy', params)
    os.system('dmesg > dmesg.lossy.log')


def main():
    if len(sys.argv) > 1:
        params = {}
        params.update(BASIC_PARAMS)
        params['r1_r2']['loss'] = 1
        mn = DetourNet(params)
        CLI(mn)
        mn.stop()
    else:
        lossy()


if __name__ == '__main__':
    main()

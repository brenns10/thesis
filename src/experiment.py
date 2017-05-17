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

import argparse
import os
import re
import subprocess
import sys
import time

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink


BASIC_PARAMS = {
    'client_r1': {'delay': '5ms', 'bw': 20},
    'r1_r2': {'delay': '5ms', 'bw': 10},
    'r2_server': {'delay': '5ms', 'bw': 20},
    'r1_r3': {'delay': '5ms', 'bw': 10},
    'r2_r3': {'delay': '5ms', 'bw': 10},
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


def disable_rp_filter(node):
    # all -> used in computing the iface value. Be sure to set to 0
    node.cmd('sysctl -w net.ipv4.conf.all.rp_filter=0')
    # default -> used as value for new ifaces. Be sure to set to 0
    node.cmd('sysctl -w net.ipv4.conf.default.rp_filter=0')
    # lo -> jsut to be sure
    node.cmd('sysctl -w net.ipv4.lo.default.rp_filter=0')
    for name in node.nameToIntf:
        node.cmd('sysctl -w net.ipv4.conf.%s.rp_filter=0' % name)


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

    ### CUT ME SOME ROUTING SLACK PLEASE
    disable_rp_filter(r1)
    disable_rp_filter(r2)
    disable_rp_filter(r3)
    disable_rp_filter(client)
    disable_rp_filter(detour)
    disable_rp_filter(server)

    return mn


def is_custom_kernel():
    output = subprocess.check_output(['dmesg'])
    return 'mptcp' in output and 'detour' in output


def setup_nat(net):
    client, detour, server = net.get('client', 'detour', 'server')
    detour.cmd('./nat_detour.py &')
    if is_custom_kernel():
        client.cmd('./client daemon ../etc/daemon-nat-vm.conf')
        client.cmd('sysctl -w net.ipv4.tcp_congestion_control=lia')
        server.cmd('sysctl -w net.ipv4.tcp_congestion_control=lia')
    else:
        time.sleep(0.5)
        client.cmd('./request.py %s %s %d %d' % (detour.IP(), server.IP(),
                                                 5201, 5201))
        return 'iperf3 -c ' + detour.IP() + ' -J'


def setup_vpn(net):
    client, detour, server = net.get('client', 'detour', 'server')
    detour.cmd('./vpn_detour.sh &')
    if is_custom_kernel():
        client.cmd('./client daemon ../etc/daemon-vpn-vm.conf')
        client.cmd('sysctl -w net.ipv4.tcp_congestion_control=lia')
        server.cmd('sysctl -w net.ipv4.tcp_congestion_control=lia')
    else:
        client.cmd('openvpn --remote %s 1194 udp --client --dev tun '
                   '--ca ../tmp/ca.crt --cert ../tmp/client1.crt '
                   '--key ../tmp/client1.key ' '--topology p2p --pull '
                   '--nobind &' % detour.IP())

        # We need to wait until the openvpn interface is up. This will also
        # give us the peer IP address, which we already configured, but it's
        # always better to dynamically determine.
        output = client.monitor()
        regexp = re.compile(r'ip addr add dev tun0 local ([0-9.]+) peer ([0-9.]+)')
        while not regexp.search(output):
            output += client.monitor()
        match = regexp.search(output)
        local, peer = match.groups()
        # For some reason even after openvpn says the interface is up, we need
        # to keep waiting a bit longer before we can use it as a route gateway.
        time.sleep(0.5)
        # We have to add a very specific routing rule here so that the iperf
        # traffic goes through OpenVPN. This is, unfortunately, necessary since
        # the iperf3 -B option does not seem to work in this case.
        client.cmd('route add -host %s gw %s' % (server.IP(), peer))


def setup_ctrl(net):
    pass


SETUP = {
    'nat': setup_nat,
    'vpn': setup_vpn,
    'control': setup_ctrl,
}


def params_easy():
    """
    In this scenario, the core links are 10 Mbit while the access links are 20.
    This means that detour routing could actually aggregate more throughput
    than a single path could.
    """
    return BASIC_PARAMS.copy()


def params_lossy():
    """
    This scenario is similar to 'easy', but there is loss along the default
    route.
    """
    d = BASIC_PARAMS.copy()
    d['r1_r2']['loss'] = 1
    return d


def params_delayed():
    """
    This scenario is similar to 'easy', but there is a high latency link across
    the default route.
    """
    d = BASIC_PARAMS.copy()
    d['r1_r2']['delay'] = '100ms'
    return d


def params_sym():
    """
    In this scenario, each link has 10 Mbit bandwidth. As a result, there may
    not be any gain by aggregating paths.
    """
    d = BASIC_PARAMS.copy()
    d['client_r1']['bw'] = 10
    d['r2_server']['bw'] = 10
    d['r3_detour']['bw'] = 10
    return d


def params_sym_lossy():
    """
    This scenario, based on symmetric, has each link with the same bandwidth.
    However, the default route is lossy. Thus, the two flows are competing for
    bandwidth and the alternative subflow needs to make up the total bandwidth.
    """
    d = params_sym()
    d['r1_r2']['loss'] = 1
    return d


def params_sym_delayed():
    """
    This scenario is based on symmetric, but the default route has high delay.
    """
    d = params_sym()
    d['r1_r2']['delay'] = '100ms'
    return d


PARAMS = {
    'easy': params_easy,
    'lossy': params_lossy,
    'delayed': params_delayed,
    'sym': params_sym,
    'sym_lossy': params_sym_lossy,
    'sym_delayed': params_sym_delayed,
}


def scenario(setup_name, params_name, trials=30):
    params = PARAMS[params_name]()
    mn = DetourNet(params)
    iperf_cmd = SETUP[setup_name](mn)
    name = 'mptcp' if is_custom_kernel() else 'vanilla'

    client, detour, server = mn.get('client', 'detour', 'server')

    filename = '%s.%s.%s.json' % (params_name, setup_name, name)
    server.sendCmd('iperf3 -s -J > %s' % filename)
    print(filename + ': ', end='')

    # sleep synchronization is the worst, except for iperf
    time.sleep(0.5)

    for _ in range(trials):
        print('.', end='')
        sys.stdout.flush()
        if iperf_cmd:
            client.cmd(iperf_cmd)
        else:
            client.cmd('iperf3 -c ' + server.IP() + ' -J')
        time.sleep(0.5)

    print()
    time.sleep(0.5)

    mn.stop()
    os.system('dmesg > dmesg.%s.log' % params_name)


def main():
    parser = argparse.ArgumentParser(description='Mininet experiment harness')
    parser.add_argument('--params', type=str,
                        default='easy,lossy,delayed,sym,sym_lossy,sym_delayed',
                        help='comma separated list of params')
    parser.add_argument('--setups', type=str, default='control,nat,vpn',
                        help='comma separated list of setups')
    parser.add_argument('--cli', action='store_true',
                        help='start a cli with the first param and setup')
    parser.add_argument('--trials', '-t', type=int, default=60)

    args = parser.parse_args()
    params = args.params.split(',')
    setups = args.setups.split(',')

    if args.cli:
        mn = DetourNet(PARAMS[params[0]]())
        SETUP[setups[0]](mn)
        CLI(mn)
        mn.stop()
    else:
        for param in params:
            for setup in setups:
                scenario(setup, param, args.trials)


if __name__ == '__main__':
    main()

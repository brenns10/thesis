"""Custom topology example

No switches, only hosts and routers connected in the following topology:

    client --- r1 ---------------------- r2 --- server
                \                        /
                 ---------  r3  ---------
                            |
                          detour

"""

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink


class DetourTopo(Topo):
    "Simple topology example."

    def __init__(self):
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
        self.addLink(client, r1, delay='5ms', bw='20')
        self.addLink(r1, r2, delay='5ms', bw='10')
        self.addLink(r2, server, delay='5ms', bw='20')
        self.addLink(r1, r3, delay='5ms', bw='10')
        self.addLink(r2, r3, delay='5ms', bw='10')
        self.addLink(r3, detour, delay='5ms', bw='20)


topos = {'detour': DetourTopo}


def clear_routes(*nodes):
    for node in nodes:
        node.cmd('ip route flush table main')


def main():
    topo = DetourTopo()
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

    CLI(mn)
    mn.stop()


if __name__ == '__main__':
    main()

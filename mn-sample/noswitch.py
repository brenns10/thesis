"""A simple custom topology that involves static routes.

    h1  ---  s2  ---  h3  --- s4  ---  h5

NB this is not very related to the thesis. It was just a stepping stone for
figuring out how to create functioning mininet topologies that have no
switches, which are capable of routing.

"""

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.topo import Topo


# These are the IP addresses assigned to each interface.
H1 = '10.0.1.1'
H3_LEFT = '10.0.1.2'
H3_RIGHT = '10.0.2.1'
H5 = '10.0.2.2'
LEFT = '10.0.1.0/24'
RIGHT = '10.0.2.0/24'


class SimpleRouteTopo(Topo):
    "Simple routing topology."

    def __init__(self):
        "Create custom topo."

        # Initialize topology
        Topo.__init__(self)

        # Add hosts and switches
        h1 = self.addHost('h1', ip=H1)
        h3 = self.addHost('h3')
        h5 = self.addHost('h5', ip=H5)

        # Add links
        self.addLink(h1, h3)
        self.addLink(h3, h5)


topos = {'simple_route': SimpleRouteTopo}


def main():
    topo = SimpleRouteTopo()
    mn = Mininet(topo=topo)
    mn.start()
    h1, h3, h5 = mn.get('h1', 'h3', 'h5')

    # H3 has multiple interfaces which are difficult to deal with in topology.
    h3.connectionsTo(h1)[0][0].setIP(H3_LEFT + '/32')
    h3.connectionsTo(h5)[0][0].setIP(H3_RIGHT + '/32')

    # Next, we'll need to delete all the routes 'helpfully' established by
    # mininet.
    h1.cmd('route del -net 10.0.0.0/8')
    h3.cmd('route del -net 10.0.0.0/8')
    h3.cmd('route del -net 10.0.0.0/8')
    h5.cmd('route del -net 10.0.0.0/8')

    # Now, create the real routing tables.
    h1.setHostRoute(H3_LEFT, h1.defaultIntf())
    h1.cmd('route add -net %s gw %s' % (RIGHT, H3_LEFT))
    h5.setHostRoute(H3_RIGHT, h5.defaultIntf())
    h5.cmd('route add -net %s gw %s' % (LEFT, H3_RIGHT))
    h3.cmd('route add -net %s dev %s' % (LEFT, h3.connectionsTo(h1)[0][0]))
    h3.cmd('route add -net %s dev %s' % (RIGHT, h3.connectionsTo(h5)[0][0]))

    # Finally, h3 is a router, so route, dammit!
    h3.cmd('sysctl -w net.ipv4.ip_forward=1')

    CLI(mn)
    mn.stop()


if __name__ == '__main__':
    main()

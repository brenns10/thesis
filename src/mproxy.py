#!/usr/bin/env python
"""
Proxy daemon which configures NAT mappings within the kernel.

This is an alternative to mproxy.c, which uses its own routing table and a
Netfilter Queue to proxy packets from CLIENT to SERVER. This daemon instead
leaves all proxying to the kernel through its built-in NAT support. By
combining SNAT and DNAT, we can achieve the desired proxy results.
"""

import os
import socket
import struct

# See doc/TERMS.md for definitions of variable names.
SNAT_COMMAND = (
    'iptables -t nat -A POSTROUTING -s {client_ip} -d {server_ip} -p tcp '
    '--dport {server_port} -j SNAT --to {detour_ip}'
)
SNAT_REMOVE_COMMAND = (
    'iptables -t nat -D POSTROUTING -s {client_ip} -d {server_ip} -p tcp '
    '--dport {server_port} -j SNAT --to {detour_ip}'
)
DNAT_COMMAND = (
    'iptables -t nat -A PREROUTING -s {client_ip} -d {detour_ip} -p tcp'
    '--dport {detour_port} -j DNAT --to {server_ip}:{server_port}'
)
DNAT_REMOVE_COMMAND = (
    'iptables -t nat -D PREROUTING -s {client_ip} -d {detour_ip} -p tcp'
    '--dport {detour_port} -j DNAT --to {server_ip}:{server_port}'
)
REQUEST_FORMAT = '!4sHH'


def myip():
    # An unfortunate hack for getting a local IP address.  This will return the
    # address of *SOME* interface that can route us to 8.8.8.8, but not
    # necessarily the *ONLY* interface that we have. This means that if this
    # runs on a computer which actually has multiple interfaces and receives
    # packets on more than one of them, I'll have to modify this. But for now,
    # it will work.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 53))
    addr = s.getsockname()[0]
    s.close()
    return addr


class MProxy(object):

    def __init__(self, port=45672, ip=None):
        """Simple class that manages IPTables rules for a NAT proxy."""
        self._port = port
        self._entries = set()
        self._ip = ip if ip else myip()

    def add_rules(self, info):
        """Add IPTables rule and record a request."""
        os.system(SNAT_COMMAND.format(**info, detour_ip=self._ip))
        os.system(DNAT_COMMAND.format(**info, detour_ip=self._ip))
        self._entries.add(self.freeze(info))

    def del_rules(self, info):
        """Delete IPTables rule and recorded information."""
        os.system(SNAT_REMOVE_COMMAND.format(**info, detour_ip=self._ip))
        os.system(DNAT_REMOVE_COMMAND.format(**info, detour_ip=self._ip))
        self._entries.remove(self.freeze(info))

    def freeze(self, info):
        """Freeze a dict (i.e. turn it into a hashable object)"""
        return frozenset(info.items())

    def thaw(self, tup):
        """Thaw a dict (i.e. turn it back into a dict)"""
        return dict(tup)

    def contains_entry(self, info):
        """Return True if we've already created a rule for this request."""
        return self.freeze(info) in self._entries

    def handle_request(self, data, addr):
        """Handle an incoming UDP request."""
        request = struct.unpack(REQUEST_FORMAT, data)
        info = {
            'server_ip': socket.inet_ntoa(request[0]),
            'server_port': request[1],
            'detour_port': request[2],
            'client_ip': addr[0],
        }
        if not self.contains_entry(info):
            self.add_rules(info)

    def clean_up(self):
        """Delete all rules we have created."""
        for frozen in self._entries:
            self.del_rules(self.thaw(frozen))

    def serve(self):
        """Bind this server to a port and serve forever."""
        # ensure that we are configured to forward packets
        os.system('sysctl -w net.ipv4.ip_forward=1')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('0.0.0.0', self._port))
        msg_size = struct.calcsize(REQUEST_FORMAT)
        try:
            while True:
                data, addr = s.recv(msg_size)
                assert(len(data) == msg_size)
                self.handle_request(data, addr)
        finally:
            # No matter what, we want to delete the IPTables rules we created.
            self.clean_up()


if __name__ == '__main__':
    MProxy().serve()

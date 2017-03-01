#!/usr/bin/env python
"""
Proxy daemon which configures NAT mappings within the kernel.

This is an alternative to mproxy.c, which uses its own routing table and a
Netfilter Queue to proxy packets from CLIENT to SERVER. This daemon instead
leaves all proxying to the kernel through its built-in NAT support. By
combining SNAT and DNAT, we can achieve the desired proxy results.
"""

from collections import namedtuple
import logging
import os
import socket
import struct
import random

import psutil

# See doc/TERMS.md for definitions of variable names.
SNAT_COMMAND = (
    'iptables -t nat -A POSTROUTING -s {cip} -d {rip} -p tcp '
    '--dport {rpt} -j SNAT --to {dip}'
)
SNAT_REMOVE_COMMAND = (
    'iptables -t nat -D POSTROUTING -s {cip} -d {rip} -p tcp '
    '--dport {rpt} -j SNAT --to {dip}'
)
DNAT_COMMAND = (
    'iptables -t nat -A PREROUTING -s {cip} -d {dip} -p tcp '
    '--dport {dpt} -j DNAT --to {rip}:{rpt}'
)
DNAT_REMOVE_COMMAND = (
    'iptables -t nat -D PREROUTING -s {cip} -d {dip} -p tcp '
    '--dport {dpt} -j DNAT --to {rip}:{rpt}'
)

# Protocol information
MPROXY_VERSION = 1
MPROXY_REQUEST = 0
MPROXY_RESPONSE = 1
REQUEST_FORMAT = '!BBxx4sHH'

# IANA suggested
MIN_EPHEM = 49152
MAX_EPHEM = 65535

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
log.addHandler(ch)

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


def is_port_open(n):
    """
    Return True if there is a TCP server listening on that port.

    This only considers non-loopback servers (i.e. remote address is not
    127.0.0.1 or ::1).
    """
    connections = psutil.net_connections('tcp')
    for conn in connections:
        if conn.laddr[0] == '127.0.0.1' or conn.laddr[0] == '::1':
            # ignore loopback
            continue
        if conn.laddr[1] == n and conn.status == psutil.CONN_LISTEN:
            return True
    return False


Request = namedtuple('Request', ['rip', 'rpt', 'dpt', 'cip'])


class MProxyError(Exception):
    pass


class MProxy(object):

    def __init__(self, port=45672, ip=None):
        """Simple class that manages IPTables rules for a NAT proxy."""
        self._port = port
        self._entries_by_dpt = {}
        self._entries_by_rem = {}
        self._entries = set()
        self._ip = ip if ip else myip()

    def add_rules(self, i):
        """Add IPTables rule and record a request."""
        sc = SNAT_COMMAND.format(**i._asdict(), dip=self._ip)
        dc = DNAT_COMMAND.format(**i._asdict(), dip=self._ip)
        os.system(sc)
        os.system(dc)
        log.debug(sc)
        log.debug(dc)
        self._entries_by_dpt[(i.cip, i.dpt)] = (i.rip, i.rpt)
        self._entries_by_rem[(i.cip, i.rip, i.rpt)] = i.dpt
        self._entries.add(i)

    def del_rules(self, i):
        """Delete IPTables rule and recorded information."""
        sc = SNAT_REMOVE_COMMAND.format(**i._asdict(), dip=self._ip)
        dc = DNAT_REMOVE_COMMAND.format(**i._asdict(), dip=self._ip)
        os.system(sc)
        os.system(dc)
        log.debug(sc)
        log.debug(dc)
        del self._entries_by_dpt[(i.cip, i.dpt)]
        del self._entries_by_rem[(i.cip, i.rip, i.rpt)]
        self._entries.remove(i)

    def preexisting_dpt(self, i):
        """Returns any preexisting dpt for the client and remote, or None."""
        return self._entries_by_rem.get((i.cip, i.rip, i.rpt), None)

    def dpt_used_by_client(self, i):
        """Returns truthy if the client has an entry with that dpt already."""
        return (i.cip, i.dpt) in self._entries_by_dpt

    def dpt_restricted(self, i):
        """Returns truthy if the dpt is restricted."""
        return is_port_open(i.dpt)

    def pick_new_dpt(self, i):
        """Picks a dpt unused by the client so far."""
        # choose a new one first, in case dpt = 0, or something
        i = i._replace(dpt=random.randint(MIN_EPHEM, MAX_EPHEM))
        while self.dpt_used_by_client(i) and not self.dpt_restricted(i.dpt):
            i = i._replace(dpt=random.randint(MIN_EPHEM, MAX_EPHEM))
        return i

    def create_request(self, data, addr):
        """Validate fields and create request."""
        version = data[0]
        if version != MPROXY_VERSION:
            raise MProxyError(
                'Request version ({}) does not match expected ({})'.format(
                    version, MPROXY_VERSION
            ))
        if len(data) != struct.calcsize(REQUEST_FORMAT):
            raise MProxyError('Data length ({}) does not match expected ({})')
        fields = struct.unpack(REQUEST_FORMAT, data)
        # [0] - version, [1] - op, [2] - rip, [3] - rpt, [4] - dpt
        if fields[1] != MPROXY_REQUEST:
            raise MProxyError(
                'Message op ({}) is not MPROXY_REQUEST ({})'.format(
                    fields[0], MPROXY_REQUEST
            ))
        return Request(
            rip=socket.inet_ntoa(fields[2]),
            rpt=fields[3],
            dpt=fields[4],
            cip=addr[0],
        )

    def create_response(self, i):
        """Create bytes response."""
        return struct.pack(REQUEST_FORMAT, MPROXY_VERSION, MPROXY_RESPONSE,
                           socket.inet_aton(i.rip), i.rpt, i.dpt)

    def handle_request(self, data, addr, sk):
        """Handle an incoming UDP request."""
        # Parse request
        i = self.create_request(data, addr)
        log.debug('Incoming: ' + str(i))

        req_dpt = i.dpt
        verb = 'ADD '
        # Choose new dpt when necessary
        if self.preexisting_dpt(i):
            # We already have a detour for cip, rip, rpt, use that!
            i = i._replace(dpt=self.preexisting_dpt(i))
            log.debug('Used preexisting dpt=%d', i.dpt)
            # NO ADD RULES, it's already there
            verb = 'ECHO'
        elif self.dpt_used_by_client(i) or self.dpt_restricted(i):
            # We already have a detour for cip, dpt, so pick new dpt!
            i = self.pick_new_dpt(i)
            log.debug('Chose new dpt=%d', i.dpt)
            self.add_rules(i)
        else:
            self.add_rules(i)

        # echo final mapping
        sk.sendto(self.create_response(i), addr)
        return i, req_dpt, verb

    def clean_up(self):
        """Delete all rules we have created."""
        for i in list(self._entries):
            self.del_rules(i)

    def serve(self):
        """Bind this server to a port and serve forever."""
        # ensure that we are configured to forward packets
        os.system('sysctl -w net.ipv4.ip_forward=1')
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('0.0.0.0', self._port))
        max_size = 512
        msg_size = struct.calcsize(REQUEST_FORMAT)
        try:
            while True:
                try:
                    data, addr = s.recvfrom(max_size)
                    i, req_dpt, verb = self.handle_request(data, addr, s)
                    log.info('%s %s to %s:%d via %d (%d proposed)', verb,
                             i.cip, i.rip, i.rpt, i.dpt, req_dpt)
                except MProxyError as e:
                    log.error('Encountered exception (%s) while handling data (%r) from %r.',
                              str(e), data, addr)
        finally:
            # No matter what, we want to delete the IPTables rules we created.
            log.info('Received exception, cleaning up!')
            self.clean_up()


if __name__ == '__main__':
    MProxy().serve()

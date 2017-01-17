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

SNAT_COMMAND = (
    'iptables -t nat -A POSTROUTING -s {CLIENT_IP} -d {SERVER_IP} -p tcp '
    '--dport {SERVER_PORT} -j SNAT --to 192.168.0.6'
)
DNAT_COMMAND = (
    'iptables -t nat -A PREROUTING -s {CLIENT_IP} -d 192.168.0.6 -p tcp --dport {DETOUR_PORT} '
    '-j DNAT --to {SERVER_IP}:{SERVER_PORT}'
)
REQUEST_FORMAT = '!4sH4sH'


def handle_request(data):
    request = struct.unpack(REQUEST_FORMAT, data)
    info = {
        'CLIENT_IP': socket.inet_ntoa(request[0]),
        'DETOUR_PORT': request[1],
        'SERVER_IP': socket.inet_ntoa(request[2]),
        'SERVER_PORT': request[3],
    }
    os.system(SNAT_COMMAND.format(**info))
    os.system(DNAT_COMMAND.format(**info))


def main(port=45672):
    # ensure that we are configured to forward packets
    os.system('sysctl -w net.ipv4.ip_forward=1')
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', port))
    msg_size = struct.calcsize(REQUEST_FORMAT)
    while True:
        data = s.recv(msg_size)
        assert(len(data) == msg_size)
        handle_request(data)


if __name__ == '__main__':
    main()

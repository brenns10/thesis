#!/usr/bin/env python
"""
Send requests to the mproxy daemon. Must run from client.

usage: mproxy_client.py DAEMON_IP SERVER_IP SERVER_PORT DETOUR_PORT
"""

import logging
import sys
import struct
import socket

MPROXY_VERSION = 1
MPROXY_REQUEST = 0
MPROXY_RESPONSE = 1
REQUEST_FORMAT = '!BBxx4sHH'

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.NOTSET)
log.addHandler(ch)

def main():
    if len(sys.argv) != 5:
        print('usage: mproxy_client.py DAEMON_IP SERVER_IP SERVER_PORT DETOUR_PORT')
        sys.exit(1)
    daemon_ip = sys.argv[1]
    request = sys.argv[2:]
    request[0] = socket.inet_aton(request[0])
    request[1] = int(request[1])
    request[2] = int(request[2])
    request = [MPROXY_VERSION, MPROXY_REQUEST] + request
    data = struct.pack(REQUEST_FORMAT, *request)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    log.debug('Sending request...')
    s.sendto(data, (daemon_ip, 45672))
    msg, addr = s.recvfrom(len(data))
    response = struct.unpack(REQUEST_FORMAT, msg)
    log.info('Received response: [%d] -> %s:%d', response[4],
             socket.inet_ntoa(response[2]), response[3])

if __name__ == '__main__':
    main()

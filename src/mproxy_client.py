#!/usr/bin/env python
"""
Send requests to the mproxy daemon. Must run from client.

usage: mproxy_client.py DAEMON_IP SERVER_IP SERVER_PORT DETOUR_PORT
"""

import sys
import struct
import socket

REQUEST_FORMAT = '!4sHH'

def main():
    if len(sys.argv) != 5:
        print('usage: mproxy_client.py DAEMON_IP SERVER_IP SERVER_PORT DETOUR_PORT')
        sys.exit(1)
    daemon_ip = sys.argv[1]
    request = sys.argv[2:]
    request[0] = socket.inet_aton(request[0])
    request[1] = int(request[1])
    request[2] = int(request[2])
    data = struct.pack(REQUEST_FORMAT, *request)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(data, (daemon_ip, 45672))


if __name__ == '__main__':
    main()

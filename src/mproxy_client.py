#!/usr/bin/env python
"""
Send requests to the mproxy daemon.

usage: mproxy_client.py DAEMON_IP CLIENT_IP DETOUR_PORT SERVER_IP SERVER_PORT
"""

import sys
import struct
import socket

REQUEST_FORMAT = '!4sH4sH'

def main():
    if len(sys.argv) != 6:
        print('requires 5 args...')
    daemon_ip = sys.argv[1]
    request = sys.argv[2:]
    request[0] = socket.inet_aton(request[0])
    request[1] = int(request[1])
    request[2] = socket.inet_aton(request[2])
    request[3] = int(request[1])
    data = struct.pack(REQUEST_FORMAT, *request)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(data, (daemon_ip, 45672))


if __name__ == '__main__':
    main()

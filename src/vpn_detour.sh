#!/bin/sh

# enable packet forwarding
sysctl -w net.ipv4.ip_forward=1

# perform NAT on traffic from openvpn
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -j MASQUERADE

# and start openvpn
openvpn --dev tun \
	--server 10.8.0.0 255.255.255.0 \
	--dh ../tmp/dh.pem \
	--ca ../tmp/ca.crt \
	--cert ../tmp/server.crt \
	--key ../tmp/server.key \
	--topology p2p \
	--push 'route "0.0.0.0 0.0.0.0 10.8.0.0 1000"'

OpenVPN
=======

The second strategy for creating detours, after simple NAT, is the OpenVPN
tunnel. Since OpenVPN gives you a TUN or TAP device (that mimics a network
device in the kernel), using MPTCP over it should be easier and "more correct"
than using the NAT.

OpenVPN seems to have two operating modes, one of which is not very well
documented. The common operating mode is the "client/server" one. This requires
configuration of TLS certificates - a self-signed CA as well as a client and
server certificate. There are also a few other keys to generate. When all is
said and done, the client and server do mutual authentication process, and then
you have a virtual LAN.

The other operating mode is a "tunnel" mode which can be done in plaintext, with
no extra keys or certificates. It simply binds a tun/tap device on one computer
to a tun/tap device on another. The trouble with this service is that the tunnel
mode is not meant to service more than one client. Also, the server and client
must have previously agreed upon IP addresses to use for their connection.

While the lightweight tunnel approach seems much better for us, the negotiaton
of IP addresses just doesn't seem reasonable - it would require us to
communicate with the server in advance, and that's just too close to the detour
method. So we will use the server approach. We can still specify that no cipher
and no message authentication is to be used, which is insecure, but that's not
really the point!

Config
------

The server uses the following options:

```
# tun and tap would both work, but tun has less header overhead since it's a
# level 3 tunnel
dev tun

# this is address / mask, because apparently openvpn is too cool for cidr
server 10.8.0.0 255.255.255.0

# diffie-hellman params, must be generated
dh dh.pem

# our own personal CA!
ca ca.crt
cert server.crt
key server.key

# could be p2p or subnet (probably)
topology p2p

# syntax NETWORK MASK GATEWAY METRIC. we're saying we can reach the entire
# internet, but we have a very high cost. hopefully the client os won't use us
# for anything other than MPTCP connections as a result.
push route "0.0.0.0 0.0.0.0 10.8.0.0 1000"
```

The client uses the following options:

```
remote ADDR
dev tun
client

ca ca.crt
cert client.crt
key client.key

topology p2p

# accept the server's pushed options
pull
```

Note that at least the server (maybe the client) will need to have
`net.ipv4.ip_forward` enabled in order for this work. Furthermore, the server
will need to have an iptables rule for NAT like so:

```
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o INTERFACE -j MASQUERADE
```

The INTERFACE is not exactly needed, especially if we're not part of a `10.*`
subnet.

Approach
--------

The approach for this is not going to be too difficult. The `client.c` program
will be extended to fork and call OpenVPN to connect to whatever detours it
wants. At startup, it will establish these connections and, when they are
established (and finished doing their mss fix) they will send the kernel a new
type of message giving it info about the new route (which is just an
ifindex/net_dev to it).

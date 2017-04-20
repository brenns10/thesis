Strategies
==========

Tunneling
---------

There are a couple ways to "tunnel" the traffic from the client to the server.

### VPN

The most obvious approach is to use a VPN connection to the detour. The VPN
should do the following:

1. Assign you an IP address within its network.
2. Give you a gateway with which to connect to the Internet.

Assuming that you avoid changing your *default* gateway to your VPNs, *and* that
none of the IP subnets overlap (theoretically this wouldn't matter as long as
*you* don't receive the same IP address from different VPNs), you now have
multiple "interfaces", just as MPTCP expects.

You can then use any path manager you would like. However, you probably would
prefer to use a path manager that will "experiment" with each VPN/detour, until
it finds the best ones.

Pros:
- No kernel modification required to use a VPN as another interface.
- Very little kernel modification is necessary. Simply write a new path manager
  similar to the "fullmesh" one (which is rather complex), which explores the
  available options.
  
Cons:
- VPN configuration can be a mess.
- Manually manage route in daemon.
- Could result in performance hit if doing TCP over TCP.
- "Fullmesh" path manager is very complex. We would need to add the complexity
  of tracking which interfaces we haven't tried yet, with the knowledge that new
  ones could be added and existing ones removed at any time. This could be
  tough.
  
Decision Factors:
- It would not be hard to come up with a test that simply uses one detour, in
  order to compare it with the NAT approach.

### NAT

A simpler way is to simply address the packet to the detour. If the detour knows
ahead of time that it will receive a connection on a port, and that it should
NAT that connection to the end server, it can act as a transparent router with
NAT. MPTCP is designed to work through NAT, so this should not affect too much.

Pros:
- Avoids overhead of VPN, as well as potential for messing up client routing
- Kernel implementation can vary in complexity:
  - simplest option - kernel tells daemon on connection
  - daemon tells kernel when to add a path
  - kernel informs daemon of path
  - all done with netlink socket

Cons:
- The detour point must be custom (rather than a standard vpn).
- Per-connection setup must occur, and this may incur an additional round trip.

Client
------

The client needs to be able to do the following:

1. Discover available detour hops
2. Request transit through a detour. This could be done in two ways:
   - Send a separate request (UDP, *mayyybe* TCP) to the detour containing the
     address and port.
   - Insert

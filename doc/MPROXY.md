MProxy Protocol
===============

Introduction
------------

In the MPTCP Detour setup, there are several possible ways which a subflow could
be routed through a different path or host. Currently we are considering two
ways in this thesis: a NAT based system and an OpenVPN based system.

In the NAT based system, a detour box configures NAT rules in the kernel, so
that TCP flows directed to the detour can be NAT'd to their final destination.
In order to configure these NAT rules, the client must initially send a request
to the detour, notifying of the intent to connect to a host and port through the
detour. The MProxy protocol is the "language" spoken by the client and daemon to
negotiate these rules.

This document describes the MProxy Protocol version 1, which is currently in an
experimental, unstable state. A Python reference implementation of the detour
end of the protocol can be found in `src/mproxy.py`, and two implementations are
included of a client (`src/mproxy_client.py` and `src/netlink_client.c`).

Protocol
--------

MProxy protocol is an application level protocol based on UDP. The detour
receives requests on UDP port 45672. The message format is as follows:

    +-----------------------------------+
    | ver(1) | op(1)  | reserved (2)    |
    +-----------------------------------+
    |           rip (4 bytes)           |
    +-----------------------------------+
    | rpt (2 bytes)   | dpt (2 bytes)   |
    +-----------------|-----------------+
    
- `ver` - protocol version, 1 byte. Set to 1.
- `op` - operation, 1 byte. Can have the following values:
  - 0 - `MPROXY_REQUEST` - request message
  - 1 - `MPROXY_RESPONSE` - response message
- `reserved` - unspecified at this time.
- `rip` - remote ip
- `rpt` - remote port
- `dpt` - detour port

Request
-------

To request a detour, clients send a request datagram to the detour machine on
UDP port 45672. The remote address and port fields contain, in network byte
order, the address which the client intends to connect to through the detour.
The detour port field contains a *proposed* port that the client will use when
addressing its TCP packets to the detour. `op` is set to `MPROXY_REQUEST`.

Requests are **idempotent**, that is, the same request repeated multiple times
will achieve the same response.

Response
--------

When a detour receives a request, it will attempt to create a NAT mapping by
following the criteria below:

1. If a mapping to that remote host and port already exists for the client, no
   new mapping is created. Instead, the existing mapping is returned.
2. If a mapping from that client and detour port already exists, a new detour
   port is chosen by the detour.
3. If local policy dictates that the requested detour port should not be used,
   then a new detour port may be chosen by the detour. See the "Security
   Considerations" section for some examples of reasons why a detour port may be
   blacklisted.
4. Otherwise, the mapping is created as requested.

The detour will send a response message containing the same remote address and
remote port, and the selected detour port. `op` is set to `MPROXY_RESPONSE`.

Special Ports
-------------

A request packet may request detour port 0 in order to ask for a dynamically
allocated port. The method of choosing the dynamically allocated port is
unspecified, provided that if a detour already exists to the specified remote
address for that client, the existing detour port should be returned rather than
a new port created. Thus, special request packets may be reordered and sent
alongside regular request packets idempotently.

Multiple Connections
--------------------

A single detour mapping allows many TCP connections to be created (since the
client will create a new ephemeral port each time it connects to the detour).
The detour will also create an ephemeral port when it connects to the remote. It
is not guaranteed that the ephemeral port created by the detour will match the
ephemeral port chosen by the client. This is not a problem because port
translation is a regular part of NAT, which MPTCP is designed to work through.

Reliability
-----------

Since UDP is not a reliable protocol, it is possible for requests and responses
to be silently dropped. The MProxy protocol has no built-in support for
reliability; instead, clients should retry requests which have received no
responses after a timeout. Since requests are idempotent, there is no danger to
the detour receiving multiple identical requests due to a dropped response. The
choice of timeout is left up to implementers.

One strategy to avoid retransmissions could be to send multiple copies of the
same request initially, rather than wait for the timeout. If packet drops were
independent with probability P, then this strategy could reduce the odds of all
packets being dropped to P^n, where n is the number of copies sent. However,
this strategy is not recommended for two reasons.

1. First, packet drops are almost certainly not independent. Sending many
   packets at a time only increases the odds of filling up routing buffers.
2. Second, clients likely will stop listening for responses after the first
   response received. Subsequent responses would likely fail with ICMP port
   unreachable messages. Although a well-designed detour server/operating system
   should be able to deal with this, unnecessary messaging like this should be
   avoided.

Security Considerations
-----------------------

Datagram-based protocols are vulnerable to forged packets.

A detour receiving a packet with a forged source address would create a NAT
entry routing the forged source address to the destination, rather than the
actual source address. However, since the attacker could not establish a
three-way handshake over TCP, the NAT route could not be used by the attacker.
However, if a client were about to connect to a TCP port on the detour machine
itself (rather than using it as a detour), a malicious third party could forge a
request from the client in order to NAT the traffic elsewhere, and potentially
pose as the detour. For this reason, a detour that has open ports for TCP
services should not allow these ports to be used as detour ports.

A client receiving a packet with a forged source address would likely drop the
packet, unless a request had already been sent to the forged source address. If
the attacker were able to observe (but not modify) packets on the client's link,
it could forge responses. The attacker's forgery could only specify a different
detour port (on the same detour server), not a detour through their own machine.
However, combining these two forgery scenarios, there is one serious attack
possible:

1. An attacker can observe the client's link and send packets to the client and
   detour, but not modify any traffic.
2. The attacker notices that a client uses the detour services. The attacker
   forges a request (using the client's address) for a detour routed to a
   malicious host. It observes the response (which is ignored by the client's
   operating system) and records the port number.
3. When the client next requests a detour, the attacker sends a spoofed
   response, using the port returned from step 2. The client accepts the
   mapping, dropping the eventual authentic response from the detour.
4. The client connects to a detour port which it believes will route to its
   ultimate destination. However, the port actually routes to the malicious
   server.
   
In the case of MPTCP, this attack could still be critical, because the malicious
attacker may have observed the initial MPTCP key exchange. The malicious host
could then authenticate itself as the MPTCP end host, and it could even
establish a subflow with the actual end host in order to echo data that flows
through it, avoiding detection by the client.

This sequence of events is very unlikely to occur, but is definitely possible.
The attacker would need to very quickly react and communicate a lot of
information to make the attack successful. However, since such vulnerabilities
are present, the OpenVPN approach may be a more safe technique for real-word
application.

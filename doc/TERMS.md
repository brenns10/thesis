Terms
=====

Hosts
-----

Since this project involves several computers working together with different
roles, it really helps to have uniform terms for each role.

- **Client:** This is the end of the MPTCP connection we're thinking from. It's
  the host which is seeking out detour routes to its destination. Typically,
  this means this is the host which initiated the TCP connection in the first
  place.
  - The client must be MPTCP capable. Furthermore, it must be running my custom
    MPTCP kernel.
- **Detour:** This is the "third party" host which is used as a relay between
  the client and server.
  - This host need not be MPTCP capable, since it merely tunnels / proxies /
    NATs packets.
- **Server:** This is the "other end" of the MPTCP connection.
  - This host must be MPTCP capable, but it need not be aware of my customized
    MPTCP kernel.

Addresses
---------

- **Client IP:** We're assuming that the client only has one interface, and this
  is the address corresponding to that interface.
- **Detour IP:** Similarly, the detour only has one interface, and this is the
  address corresponding to that interface.
- **Detour Port:** When the client is attempting to tunnel its traffic through
  the detour, it addresses its packets to the detour IP, and it selects a TCP
  destination port as well. This detour port need not be the same as the server
  port, so that the client may make multiple connections to the same server and
  port through the same detour.
- **Server IP:** The server may have multiple interfaces, we don't know. But
  this address corresponds to any of the addresses that we, the client, are
  aware of.
- **Server Port:** This is the port on the server that the client initially
  connected to.
  
Note a few port numbers which are *absent* from the above list:

- The ephemeral port number assigned to the client's source port number, on the
  master flow or any subflow.
- The ephemeral port number assigned to the detour's source port number.
  - You may think that this should be the same as the client's ephemeral port.
    Normally, it might be. However, the Linux kernel NAT may have to alter this
    port number in order to avoid collisions.

Netlink Protocol Documentation
==============================

Here I will document my netlink communication protocol.

Commands
--------

### DETOUR_C_ADD

Add a detour entry. A detour entry consists of:

- A detour IP - `DETOUR_A_DETOUR_IP`
- A detour port - `DETOUR_A_DETOUR_PORT`
- A server IP - `DETOUR_A_REMOTE_IP`
- A server port - `DETOUR_A_REMOTE_PORT`

### DETOUR_C_DEL

Remove a detour entry. This will probably only delete the entry from the list,
without terminating any subflows through this detour.

- `DETOUR_A_DETOUR_IP`
- `DETOUR_A_DETOUR_PORT`
- `DETOUR_A_REMOTE_IP`
- `DETOUR_A_REMOTE_PORT`

### DETOUR_C_REQ

Request a detour. The kernel sends this command to a multicast group, and any
interested daemon may receive it.

- `DETOUR_A_REMOTE_IP`
- `DETOUR_A_REMOTE_PORT`

### DETOUR_C_STAT

Provides statistics about a particular connection. If nothing else, gives RTT. I
haven't completely finished thinking this one out.

Attributes
----------

### DETOUR_A_DETOUR_IP

IPv4 address of a detour.  Type is U32. Should be in network byte order.

### DETOUR_A_DETOUR_PORT

TCP port of a detour.  Type is U16. Should be in network byte order.

### DETOUR_A_REMOTE_IP

IPv4 address of the server (remote end of connection). Type is U32, network byte
order.

### DETOUR_A_REMOTE_PORT

TCP port of the server (remote end of connection). Type is U16, network byte
order.

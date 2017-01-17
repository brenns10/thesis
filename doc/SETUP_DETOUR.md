Detour Setup
============

This document describes how to get the detour point running. Unlike the client,
there is no need for a virtual machine, and the requirements are dramatically
simpler.

It is entirely possible to run the detour on the same machine as the client
virtual machine. Just note that an additional interface (e.g. wireless, or yet
another emulated NIC on the bridge) is required for the host machine.

Prerequisites
-------------

The detour point needs to run a semi-recent version of Linux. I'm using Arch
Linux so my main concern with this document is describing setup for Arch.

You'll need the following packages installed:

- `python`

Setup
-----

Thankfully, there is no complex setup for the detour. The code is located within
this `thesis` repository, in [src/mproxy.py](../src/mproxy.py). Simply run the
following:

```bash
sudo python mproxy.py
```

Note that this script will enable packet forwarding in your kernel. This is
because the proxy works by creating iptables rules which perform NAT.

To request a tunnel, use [src/mproxy_client.py](../src/mproxy_client.py). This
tool works as follows:

```bash
python mproxy_client.py DETOUR_IP CLIENT_IP DETOUR_PORT SERVER_IP SERVER_PORT
```

The meaning of all these arguments:
- DETOUR_IP - the ip address of the detour point. This is just so the program
  knows where to send the UDP request, so you can use "localhost" since you're
  normally running the command on the same machine as the detour.
- CLIENT_IP - ip address of the client
- DETOUR_PORT - the port number that the client will connect with
- SERVER_IP - ip address of the end server the client wants to talk to
- SERVER_PORT - port on the end server

So a typical run might work something like this:

```bash
python mproxy_client.py localhost 192.168.0.201 80 130.104.230.45 80
```

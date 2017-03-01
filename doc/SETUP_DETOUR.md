Detour Setup
============

This document describes how to get the detour point running. Unlike the client,
there is no need for a virtual machine, and the requirements are dramatically
simpler.

I have not successfully gotten everything working with the detour on the same
machine as the client, which is not a problem, but it does mean that you'll
need to have a second computer for setting up the detour.

Prerequisites
-------------

The detour point needs to run a semi-recent version of Linux. I'm using Arch
Linux so my main concern with this document is describing setup for Arch.

You'll need the following packages installed:

- `python` (i.e. python 3)
- `iptables`
- the `psutil` python package, possibly named `python-psutil` in your package
  manager

Setup
-----

Thankfully, there is no complex setup for the detour. The code is located within
this `thesis` repository, in [src/detour.py](../src/detour.py). Simply run the
following:

```bash
sudo python detour.py
```

Note that this script will enable packet forwarding in your kernel. This is
because the proxy works by creating iptables rules which perform NAT.

To request a tunnel, use [src/request.py](../src/request.py). This tool works as
follows:

```bash
python request.py DETOUR_IP CLIENT_IP DETOUR_PORT SERVER_IP SERVER_PORT
```

The meaning of all these arguments:
- DETOUR_IP - the ip address of the detour point. This is just so the program
  knows where to send the UDP request, so you can use "localhost" since you're
  normally running the command on the same machine as the detour.
- CLIENT_IP - ip address of the client
- DETOUR_PORT - the port number that the client proposes to connect with
- SERVER_IP - ip address of the end server the client wants to talk to
- SERVER_PORT - port on the end server

So a typical run might work something like this:

```bash
python mproxy_client.py localhost 192.168.0.201 80 130.104.230.45 80
```

The main usage of the `detour.py` server is with `client.c`, which is run on the
client. See [TEST.md](TEST.md) for documentation on a complete test setup.

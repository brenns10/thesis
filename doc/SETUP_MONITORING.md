Monitoring Setup
================

In order to monitor network traffic, Wireshark is typically your best friend.
However, once you start getting into packet mangling and NAT, the picture from
your laptop's NIC ceases to be good enough. So, I found it useful to do a TCP
dump on my router itself, and pipe the result into a Wireshark instance.

Router Setup
------------

I've been running ASUSwrt-Merlin, a custom firmware for my ASUS RT-N66U router.
It was very easy to set up (I'm sure instructions are out there). If you have a
flash drive connected to your router formatted to ext3, you can set up a package
manager called entware-ng, and use that to install `tcpdump`. Then you can pipe
packet captures over SSH into a named pipe, and have Wireshark listen to that
named pipe.

Here's the initial setup of the router:

```bash
# First, format and mount the flash drive
entware-setup.sh
# Follow instructions
opkg install tcpdump
```

Running Packet Captures
-----------------------

Now, with SSH access to the router, you can run a packet capture like so:

```bash
mkfifo /tmp/capture
ssh admin@192.168.0.1 tcpdump -U -s0 -n -w - -i br0 "host 130.104.230.45" >/tmp/capture
```

- Option `-U` enables "packet buffering" so that we see each packet as it
  arrives.
- Option `-s0` instructs tcpdump to include 262144 bytes of data from each
  packet.
- Option `-n` instructs tcpdump not to convert addresses to names
- `-w -` instructs tcpdump to "write" capture to a PCAP file on stdout rather
  than print it in a human readable format
- `-i br0` is specific to my router, instructing tcpdump to capture on the LAN
  interface rather than the WAN interface. This way I can see packets before the
  router performs NAT.
- `"host 130.104.230.45"` is a filter for tcpdump.

The result is piped into the fifo we created. To view it in Wireshark, we can
simply run:

```bash
wireshark -k -i /tmp/capture
```

Note that whenever you restart the capture you must restart Wireshark and vice
versa.

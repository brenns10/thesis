Captures
========

This directory contains packet captures for a sample run of several Mininet
experiment IPerf sessions. I only included runs which are MPTCP and have
multiple subflows, because the purpose here is to determine how much data went
along each subflow. Since the connections used the Lowest RTT First scheduler,
we can be certain that there was no redundancy and therefore that the sequence
numbers are a good indicator of the amount of data along each subflow.

There are several types of file:

- `.pcap` - packet captures, produced *at the server*. This is important because
  the server is the only one that get's a 100% compatible view of the MPTCP
  connection. But, since the server is on the other side of some high-latency
  links (in the delay experiments) sometimes we get an incomplete picture... In
  particular, segments traversing the lossy link were sent over 100ms before
  their timestamp.
- `.xpl` - xplot files, produced by a proprietary tool. Run `xplot file.xpl` to
  view them. The arrows represent segments of data. The squares represent
  acknowledgements. The green line is the cumulative ACK.
- `.mapping.txt` - contains the mapping of colors to flows on the xplot file
- `.summary.txt` - the short-form output from tcptrace
- `.detail.txt` - the long-form output from tcptrace

Can produce all outputs by running:

    for x in *.pcap; do ../capplot.sh "$x"; done

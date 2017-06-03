Param Validation
================

This data is a cursory glance over other potential loss or latency values, to
provide a bit of basis for the selection of 1% loss, 100ms latency.

As it turns out, they were good choices. We don't see TCP performance degrade at
0.5% loss, but we do see degradation at 1%. 2% would have been alright, but it
degrades a lot more. By 5%, throughput is reduced to 2-3 Mbps.

Similarly, for latency, 20 and 50 ms aren't enough to see any visible
degradation in performance. It's not until 100 ms that we see a drop in TCP
performance.

In the core-limited network, the bandwidths are still additive.

Source
======

This directory contains source code. Here is a directory listing:

- `Makefile` - for compilation of c files

- `client.c` - the client daemon!
- `nat_detour.py` - The NAT detour script
- `vpn_detour.sh` - The VPN detour script

- `experiment.py` - Python script for the Mininet experiment
- `make_captures.sh` - Bash driver script for mininet experiments that produce
  packet captures
- `mn_experiment.sh` - Bash driver script for mininet experiments
  (`doc/MN_EXPERIMENT.md`)
- `mn_param_range.sh` - Bash driver script for mininet experiments on extended
  parameter ranges
- `aws_experiment.py` - runs aws ec2 experiment (`doc/AWS_EXPERIMENT.md`)

- `nsdo.c` - A utility that helps with running commands within a net namespace.
- `request.py` - A utility script that creates a NAT detour request.
- `vido_init.sh` - A utility script that works around an issue with Iperf on
  vido. This is useful in debugging/development settings only. You can disregard
  it unless you're using my development setup.

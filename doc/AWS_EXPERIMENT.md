AWS Experiment
==============

This documents the AWS experiment setups I have created.

LightSail Experiment
--------------------

The lightsail experiment aimed to be simple and fast to set up. True to its
intention, I got it working in only a couple hours. Here's a step by step guide:

1. At the Lightsail control panel, create three instances. You need to do it one
   at a time so that you can place each instance into a separate AWS
   availability zone. Make sure to use the contents of `etc/aws_exp_setup.sh` as
   a startup script.

2. Create 3 static IPs, assigning each to an instance.

3. Allow networking on all TCP and UDP ports for each instance.

4. (Optional) Have DNS set up for a subdomain. Give each static IP a descriptive
   name (client, detour, server).

5. Each instance should reboot once the initialization is complete. SSH into
   each of them. Edit a client NAT/OpenVPN config so that it uses the correct IP
   address (no hostnames). Run the following commands:

       # server
       iperf3 -s

       # detour
       cd src
       sudo ./nat_detour.py
       # or
       sudo ./vpn_detour.sh

       # client
       cd src
       iperf3 -c server.thesis.brennan.io
       sudo ./client daemon ../etc/daemon-nat-vm.conf # whatever config
       iperf3 -c server.thesis.brennan.io

This all works very nicely, but there's a critical flaw to this setup. The
point of this experiment is to be large scale, and all across the internet.
Instead, this is only within Amazon's private datacenter network. While that's
better than a completely simulated network (I think), it's not actually
traversing the "open internet". So my next step is to go more complex.

EC2 Experiment
--------------

LightSail is only available in one AWS region. But it is really just a
combination of the other AWS services - EC2, EBS, etc. So I can do an equivalent
experiment using those, and distribute each host across multiple datacenters,
forcing their traffic to traverse the general Internet.



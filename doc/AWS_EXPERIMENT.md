AWS Experiment
==============

This documents the AWS experiment setups I have created. You'll need to have
created a `vm.tar` - see `doc/VM_TAR.md`.

LightSail Experiment (PROBABLY NOT WHAT YOU WANT, SEE NEXT SECTION)
-------------------------------------------------------------------

This was my first AWS experiment, based on Lightsail. At the time, Lightsail was
only available in one AWS region, so it was not suitable for real
experimentation. However, I've preserved this documentation for posterity. If
you're looking for the experiments done in the paper, go on to the next section
for the EC2 experiments.

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

The EC2 experiment is implemented in `src/aws_experiment.py`. This script
automatically launches several EC2 instances and runs IPerf 3 sessions. To do
so, it depends on the `boto3` python library for AWS, and the `paramiko` library
for SSH. You'll probably want to do a `pip install boto3 paramiko`, potentially
inside of a virtualenv.

Furthermore, you'll need to have an AWS IAM set up which has proper permissions
to create EC2 instances, etc. I simply used a root IAM which has access to
everything.

Finally, you'll need to use the AWS console to upload your computer's SSH public
key to AWS, in *each region of the experiment* (us-east-1, us-east-2,
us-west-1). Use the same name in each region. Then, when you run the AWS
experiment, specify the AWS key name and the filename of the private key using
the environment variables `KEYPAIR` and `KEYFILE`.

*Most critically of all:* the EC2 experiment instances need a way to get access
to the `vm.tar` you created. The easiest way to do this was to have them
download it from some Internet-accessible location (this is done in the AWS
setup scripts: `etc/aws_exp_setup*`). You'll want to place your `vm.tar` file in
an Internet accessible location and modify the URL I have in the scripts, if you
decide to change anything. The `vm.tar` file I have hosted in the current
scripts is from the thesis, and it will probably be there for quite a while. But
I make no guarantees.

So, assuming you have your Python and AWS environment properly configured, the
commands below will do the trick:

    KEYPAIR=aws_name KEYFILE=/home/youruser/.ssh/id_rsa ./aws_experiment.py
    KEYPAIR=aws_name KEYFILE=/home/youruser/.ssh/id_rsa ./aws_experiment.py vanilla

The first command runs experiments on MPTCP, the second command runs the same
experiments using "vanilla TCP". They take probably two hours (?). At the end,
the script will pause in an IPDB debugger so you can check on stuff (SSH into
the machines, etc). When you use the `c` command (continue) in the debugger, the
experiment will shut down everything and destroy your AWS instances.

In case you do something funky that results in the script crashing, there's a
real possibility of leftover AWS instances hanging around, which equals lots of
money being charged. Use the following command to clean up all resources used by
the experiments:

    ./aws_experiment.py cleanup

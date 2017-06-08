ETC
===

This directory contains a real weird collection of things, but they're all
necessary to make everything work. Since there are so many inter-dependencies in
the experiment code stuff, there's no way to organize this stuff without causing
all sorts of issues.

Everything in this directory gets packaged up into the VM tarball.

AWS Setup Scripts
-----------------

    aws_exp_setup.sh
    aws_exp_setup_vanilla.sh

These scripts are used by `src/aws_experiment.py`. They are provided to AWS and
they are run immediately after the EC2 instances are created, setting them up
for experiments.

See also `doc/AWS_EXPERIMENT.md`

Client Daemon Configs
---------------------

    daemon-nat-home.conf
    daemon-nat-vm.conf
    daemon-vpn-home.conf
    daemon-vpn-vm.conf

These are all different daemon configurations I used at one time or another. The
home configurations were used within my home network for initial validation. The
vm ones are used in the Mininet experiments.

Kernel Config Fragments
-----------------------

    debug.frag
    mininet.frag
    mptcp.frag
    vido.frag

These can be applied on top of a base Linux kernel configuration (using the
merge config script within the kernel source tree). All are necessary for my
debugging config. Only `mptcp` and `mininet` are necessary for release builds.
See `doc/AWSBUILD.md` and `doc/KERNEL.md`.

Complete Kernel Configurations
------------------------------

    kernel.config
    kernel_detour.config
    ubuntu_14.02_4.2.0-27.config
    ubuntu_custom.config

The ones named `kernel.config` and `kernel_detour.config` are outdated and not
used. The `ubuntu_14.02_4.2.0-27.config` one is the base configuration for my
release kernel. The `ubuntu_custom.config` is the actual configuration for my
release kernel.

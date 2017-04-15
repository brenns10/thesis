Thesis
======

This repository holds all the work for my Master's thesis, including code,
references, documentation, and of course the thesis itself.

Overview
--------

The goal of this project is to create a system which can allow users to improve
the reliability of a connection by using MPTCP to tunnel the connection through
another detour point.

Documentation
-------------

I've discovered that there is no way to complete this project without lots of
documentation about how to do the things I'm doing. Therefore I'm always
maintaining a directory full of documentation.  [Here](doc/) is the root
of that documentation.

Manifest
--------

For experimentation, the important files you must have are:

1. tmp/linux-firmware-image.deb
2. tmp/linux-image.deb - both of these are created by compiling my MPTCP kernel
   with `make deb-pkg` on a ubuntu dev machine, with the ubuntu kernel config
   found in `etc/`
3. `src/*` everything in src gets copied over
4. `etc/*` everything in etc gets copied over
5. `setup.sh` sets up the experiment VM afterwards

The program `pkg.sh` packages these up.

To summarize the experiment VM creation procedure:

1. Import the mininet VM into your hypervisor of choice.
2. Start it with host-only networking, to copy over vm.tar.
3. Reboot it with NAT networking, and log in.
4. Untar with the commands:

       mkdir thesis
       tar xf vm.tar -C thesis

5. Then execute:

       cd thesis
       ./setup.sh
       sudo reboot

6. Make sure to hold shift during GRUB in order to select the custom kernel.
7. Run experiment, which starts by going:

       sudo python thesis/src/detour_topology.py

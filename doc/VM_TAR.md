Virtual Machine Tarball
=======================

For either form of experiment, you must create this bundle (there may already be
a bundle present in the archival version of this directory). The script `pkg.sh`
in the root directory is responsible for creating this file. It will bundle up
several files:

1. `tmp/linux-firmware-image.deb` and `tmp/linux-image.deb` - these are created
   by running `make deb-pkg` in a properly configured Linux source tree with the
   path manager patch applied
3. `src/*` everything in src gets copied over
4. `etc/*` everything in etc gets copied over
5. `setup.sh` is a setup script for Mininet experiments

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

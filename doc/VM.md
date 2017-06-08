Virtual Machine
===============

Although the qemu virtual machine is great for local development, it's not the
best for deploying, both on real-world machines and on more complete virtual
machine environments.

To this end, I have a working Ubuntu 14.04 kernel build pipeline. This is done
via the AWS build machine that is [documented](AWSBUILD.md). It will provide you
with some linux-firmware-image and linux-image deb packages.

My standard virtual machine image for experiments comes directly from the
mininet Ubuntu 14.04 image. Import that into your favorite hypervisor. Setup
networking (doesn't need to be fancy, I use NAT plus a port-forward for SSH). On
your host:

    # from thesis directory
    ./pkg.sh

This will build the file `vm.tar`. Go ahead and scp that over to the VM. Untar
it with the following command:

    tar xf pkg.sh

This untars into the homedir. Next, use my setup script:

    ./setup.sh

This will install the custom kernel and do any other necessary setup items. Once
it completes, all you will need to do is reboot. Make sure to hold shift during
startup so that GRUB will give you the option to select your new kernel.

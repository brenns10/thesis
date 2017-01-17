Client Setup
============

This document describes the steps necessary to set up my environment. I intend
to keep it completely up-to-date so that starting fresh would require only
following the steps described in this document.

Prerequisites
-------------

You must be running Arch Linux, and you ought to have the following packages
installed:

- `bridge-utils`
- `python`
- `qemu`
- `qemu-arch-extra`
- `abs`

An ethernet port is required. It should be connected to a router which runs a
DHCP server with no "funny business" (i.e. MAC address registration). Wi-Fi will
not work because it is too difficult to create virtual wireless interfaces.

One thing that shouldn't be strictly necessary, but won't hurt to do, is to
place all repositories in `~/repos`.

Kernel
------

The client kernel is based on the MPTCP kernel. You'll need a git clone of it:

```
git clone --depth=1 git://github.com/multipath-tcp/mptcp.git
```

You'll also need to use the included [kernel config](../etc/kernel.config) to
compile the kernel. I intend to provide more documentation (likely in a separate
file) about the configuration I have created, but currently I have none.

Once you have the config in place, it should be as simple as `make` to get your
kernel all compiled.

Virtualization
--------------

The client kernel is run within a virtual machine. This dramatically speeds up
development (no need to reboot to test changes). Rather than using a mainline VM
software such as VirtualBox, I use qemu. With qemu, I can do development and
builds on the host machine, and easily boot the resulting kernel on top of my
existing filesystem. To achieve this, I use a wrapper script
called [vido](http://github.com/brenns10/vido). My fork adds the ability to use
bridged networking in the virtual machine, so that the VM may have multiple
NICs.

### Installation

It is not possible to use vido within a virtual environment. Therefore, you'll
have to install it globally. Since my fork is not published on PyPI, you'll need
to clone it and install it manually:

```
git clone git@github.com:brenns10/vido.git
cd vido
sudo python setup.py install
```

If any modifications are made, you must reinstall in the same way!

### Patching Python

A bug in Python 3.6 breaks vido. For reference, see the
Python [bug](https://bugs.python.org/issue29208)
and [fix](https://hg.python.org/cpython/rev/0a55e039d25f/). Unfortunately, the
fix is not yet released yet (it should be released in 3.6.1). Until then, Python
must be patched. Fortunately, with Arch, the packaging process is simple and we
can modify the system Python installation with the correct patch. Supporting
files are located in the [etc/python/](../etc/python/) directory. Change into
that directory and run the following commands to build and install a patched
Python:

```bash
makepkg -s --skippgpcheck --nocheck
# -s will install build dependencies
# --skippgpcheck will not verify pgp signatures
# --nocheck skips some of the very lengthy test suites
sudo pacman -U python-3.6.0-3.pkg.tar
# may have a '.xz' extension
```

### Host Setup

The following commands set up bridged networking on the host. The changes will
be lost on reboot, so make sure that you run them each time you boot your host
machine (more likely, each time you sit down to do development).

```bash
sudo brctl addbr bridge0
sudo brctl addif bridge0 enp0s25  # use your ethernet adapter's name
```

It may also help to run this
(see
[here](https://wiki.archlinux.org/index.php?title=Network_bridge&redirect=no)),
however I have not done A/B tests to verify whether this changes anything.

```bash
sudo modprobe br_netfilter
```

You'll also need to create a weird little file that instructs qemu that it's ok
to use your bridge. `/etc/qemu/bridge.conf`:

```
allow bridge0
```

If you have trouble, keep in mind that you ought to disable any host connections
on the ethernet adapter, so disconnect NetworkManager and make sure you don't
have a dhcpcd running on that adapter. Also make sure that the bridge interface
is marked up:

```
sudo ip link set up dev bridge0
```

Running
-------

At this point you ought to be all set up. The checklist is as follows:

- You have the MPTCP kernel built.
- You have vido installed and a patched Python interpreter.
- You have added the network bridge and connected it to your ethernet adapter.

Now you can boot the VM with:

```bash
vido --kvm --kernel ~/repos/mptcp/arch/x86_64/boot/bzImage --bridge bridge0 bridge0 -- sh
```

This instructs vido to boot your kernel using qemu with the Linux KVM module. It
also instructs vido to create *two* ethernet adapters, both from the bridge0
interface we created earlier. When the VM is booted, DHCP servers will be
launched on each emulated adapter. Then, `sh` is called within the new kernel
and you are free to do whatever you wish. You may want to check on your IP
addresses with `ip addr`.

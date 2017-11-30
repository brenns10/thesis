Thesis
======

This repository holds all the work for my Master's thesis, including code,
references, documentation, data, and of course the thesis document itself.

Overview
--------

The goal of this project is to create a system which can allow users to improve
the reliability of a connection by using MPTCP to tunnel the connection through
another detour point.

It's implemented within the Linux kernel, so applications may use it without
modification.

You can find PDFs of the paper and slides, as well as pre-built VM images, on my
website: https://brennan.io/thesis

Components
----------

The thesis has three major products:

1. A custom path manager for the MPTCP Linux kernel. This is included in this
   repository as a patch file, which may be applied onto any MPTCP source tree
   (well, it has been tested on 0.91 and 0.93). The file is located in:

       src/path-manager.patch

   As you might guess, I did not actually work on the path manager in patch
   format. I forked the MPTCP Linux kernel and developed on my own branch. You
   can find that repository here:

       https://github.com/brenns10/mptcp

   The patch included is exactly the diff containing all of my own changesets.

2. A client program which interacts with the kernel via netlink sockets. This
   is included in C source at:

       src/client.c

   It (along with one other item) may be built by invoking `make` in the `src`
   directory. You must install the libconfig-dev and libnl-genl-3-dev pakcages
   to properly build the C sources.

   After building, it may be invoked by `./client [subcommand]`. Refer to the
   help subcommand for a listing of the subcommands. Generally, you should run
   this as root, and the "daemon mode" is the one which will do the main task of
   listening for kernel detour requests and replying. It requires a config file,
   examples of which are located in `etc/*.conf`. A representative example of
   running the client daemon might be:

       sudo ./client daemon ../daemon-nat-vm.conf

3. Two "detour" implementations: OpenVPN and NAT. The NAT detour is implemented
   in Python 3, requiring the `psutil` module as well as the linux `iptables`
   command installed. It is located at:

       src/nat_detour.py

   It may be invoked as:

       sudo python3 nat_detour.py

   The OpenVPN detour is implemented as a shell script wrapping the OpenVPN tool.
   You must, obviously, have that installed. Similarly, it is located at:

       src/vpn_detour.sh

   And it may be invoked as:

       sudo ./vpn_detour.sh

These three components, combined with at minimum 3 hosts (a client, detour, and
server) form the basic setup for the thesis. Components 1 and 2 run together on
the client host (a custom MPTCP host). Component 3 runs on a detour host, which
need not understand MPTCP, but must run Linux and have OpenVPN available. The
server is unmodified, and it need only run a compliant MPTCP implementation.

Experiments
-----------

There are two experimental setups in the thesis paper: Mininet, and AWS.

### Mininet

(See also `doc/MN_EXPERIMENT.md`)

The "Mininet" experiments run inside the Mininet framework, ideally within a
virtual machine that has the custom MPTCP+detour path manager kernel installed.
Such a virtual machine may be found alongside this README as `vm.ova`, which is
suitable for import into your favorite hypervisor. The `src`, `etc`, and `tmp`
directories of this thesis are directly included within that VM at the home
directory. The username and password are both "mininet".

The Mininet experiments are implemented within `src/experiment.py`. The file
`src/mn_experiment.sh` acts as a driver script, calling this experiment for each
experimental setup. This should be run from the `src` directory, as root. It will
produce several JSON outputs similar to the ones stored in subdirectories of
`data`. See documentation of that folder for more information.

### AWS

(See also `doc/AWS_EXPERMIENT.md`)

The AWS experiments do not run within the Mininet virtual machine. Instead, a
driver script will bring up AWS virtual machines in different regions, connect
via SSH, and remotely conduct an experiment on all of them.

This driver script is `src/aws_experiment.py`. It requires some familiarity with
the AWS ecosystem. In particular, you should have:

1. The Python boto3 and paramiko packages installed
2. An AWS account and a very well-privileged IAM configured to work with Boto
3. An SSH key pair imported into every EC2 region the experiment uses (us-west-1,
   us-east-2, and us-east-1). You'll need to adjust the KEYPAIR and KEYFILE
   variables accordingly. You'll also need to adjust the `etc/aws_setup*` scripts
   with appropriate public keys to allow your computer to SSH into them.
4. Configure the default security group in your AWS account to allow ingress on
   any port. (See docstring of `src/aws_experiment.py`).

Additionally (not related to AWS), you must host `vm.tar` (see Building Blobs
below) in an Internet-reachable location. This (and the above) is documented in
the `doc/AWS_EXPERIMENT.md` file.

You may run the AWS experiment as so:

    python3 aws_experiment.py

This runs the experiment using mptcp, with (1) no detour, (2) NAT detour, (3) VPN
detour. To run the experiment with vanilla TCP:

    python3 aws_experiment.py vanilla

This runs (1) across the default route, (2) tunneled via the NAT detour, and (3)
through the VPN detour.

Building Blobs
--------------

The above instructions assumed that you have several files which are included
in the cluster41 archival, but not in Git normally. Instructions for how to
(re)create them are below:

- `tmp/linux-firmware-image.deb` and `tmp/linux-image.deb` are the Debian packages
  for my custom version of MPTCP v0.91. You can create your own by applying the
  path manager patch to an appropriate MPTCP tree, configuring the kernel, and
  finally compiling it. Some pointers are discussed in `doc/AWSBUILD.md`, which
  describes my "cloud" build machine that I used to build Debian packages.
- `vm.tar` is a tarball. It contains the above packages and some other files. See
  `doc/VM_TAR.md` for instructions on generating it, and then on using it to to
  provision your own VM image.
- Speaking of a VM image, `vm.ova` is the final piece of the puzzle. You should
  start with a Mininet Ubuntu VM image (see their Github or web site). See my docs
  in `doc/VM.md` and `doc/VM_TAR.md` describing building the image.

You may also find pre-made versions of these files at my website:
https://brennan.io/thesis

Documentation
-------------

The `doc` folder contains a mix of up-to-date documentation that can help you,
and outdated docs I wrote for myself early in the process, which refer to non-
existant files and other fun stuff. Generally, if I link to it in this README,
it should be reasonably up-to-date.

You will also find a README in most directories, giving some context on what is
contained in each directory.

Data
----

See `data/REAMDE.md`

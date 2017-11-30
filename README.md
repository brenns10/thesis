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

Documentation
-------------

There's a ton of background documentation located in the `doc` folder. Much of
it may not be relevant to those wishing to reproduce/rebuild my results, since I
used this directory to hold useful commands and other goodies mostly relevant to
me. To guide the future visitor through the major pain points of reproduction,
here are some links to pieces of documentation. Each folder should also contain
a README explaining things, in case you find yourself lost.

1. `src/path-manager.patch` - contains a patch based on the 0.91 MPTCP Linux
   kernel to include my path manager.

   To obtain a usable version of the customized Linux kernel, you will need to
   apply this patch, configure the kernel, and build it. Configuration is an
   annoying process. I discuss configuring a "debugging/development" kernel in
   `doc/KERNEL.md`. I discuss configuring and building a "release" kernel in
   `doc/AWSBUILD.md`.

   Or you can simply use my `tmp/linux-image.deb` and
   `tmp/linux-firmware-image.deb`. These are large and not stored in git, but
   are stored in the archival version of this repository, and on my website:

   https://brennan.io/downloads/linux-image.deb

   https://brennan.io/downloads/linux-firmware-image.deb

2. To run any kind of experiment, you will need to create `vm.tar`, a tarball
   containing the debian packages and source code for experiments. See
   `doc/VM_TAR.md` for instructions you must follow.

   Or you can use the included `vm.tar` (included with the archival version of
   this repository).

   Or you can download it from https://brennan.io/downloads/vm.tar

3. To run Mininet experiments, follow `doc/MN_EXPERIMENT.md`

4. To run AWS experiments, follow `doc/AWS_EXPERIMENT.md`

Data
----

See `data/REAMDE.md`

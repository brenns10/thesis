Kernel
======

Kernel development is a new world and it's worth documenting. This document
includes information about how I configured my "development kernel". Having a
development kernel which is quick to boot and test, and quick to recompile (with
very small configuration) is really important.

Virtual Machine
---------------

My virtual machine setup (with vido) is documented here:

https://brennan.io/2017/03/08/sane-kernel-dev/

Vido depends on qemu, a pretty nice virtualization system. The configuration
stuff below describes how I configured my source tree for running within Vido.
See `AWSBUILD.md` for more description of how I configured and built the kernel
for "production" uses.

Configuration
-------------

- Make targets for creating new configs:
  - `allnoconfig` - everything set to no (this would be hard to get to work)
  - `allyesconfig` - everything set to yes
  - `alldefconfig` - everything set to default. I'm not sure where these
    defaults come from, but they seem to be more minimal than `defconfig`
- Make targets that will update existing configs:
  - `xconfig` (my preference)
  - `oldconfig` - update with new options in source
  - `kvmconfig` - adds kvm guest stuff
- Scripts
  - `scripts/kconfig/merge_config.sh`

Configurations are really hard to deal with because there's so much that I don't
know about the kernel and therefore about what each option means. Messing up the
configuration means either long build times or weird errors and missing
features.

You can make configurations consistent by copying the generated `.config`, but
this is concerning because it isn't minimal, and I don't have a good
understanding of how to reproduce it (I don't even remember how I made the
current config).

A better way is to merge fragments of configurations on top of the allnoconfig.
Currently I have several fragments in my `etc/` folder.

- `vido.frag` - requirements for vido
- `debug.frag` - debugging options
- `mptcp.frag` - configuration of MPTCP

From the root of the linux directory, we can build a configuration as follows:

```bash
scripts/kconfig/merge_config.sh -n \
    arch/x86/configs/kvm_guest.config \
    ../thesis/etc/*.frag
```

Benchmarks
----------

Comparisons of build time and kernel size for various configurations.

- Merged configuration, based on alldefconfig

        Setup is 15740 bytes (padded to 15872 bytes).
        System is 2351 kB
        CRC a2b9d51a
        Kernel: arch/x86/boot/bzImage is ready  (#26)

        real	3m1.687s
        user	10m6.257s
        sys	0m38.187s

- Merged configuration, based on allnoconfig

        Setup is 15708 bytes (padded to 15872 bytes).
        System is 1524 kB
        CRC 4ac41c26
        Kernel: arch/x86/boot/bzImage is ready  (#27)

        real	2m13.621s
        user	7m19.687s
        sys	0m29.013s

- Old configuration

        Setup is 15772 bytes (padded to 15872 bytes).
        System is 6116 kB
        CRC a6a39451
        Kernel: arch/x86/boot/bzImage is ready  (#25)

        real	6m23.239s
        user	20m37.223s
        sys	1m12.457s

Thus we use the merged configuration based on allnoconfig.

Configuration Oddities
----------------------

Since I start with the most basic configuration possible, and I add only what I
need, sometimes I encounter errors that I need to address. Thus, there are quite
a few odd configuration options I have enabled in the fragments within `etc`.

For instance, I have `CONFIG_PROC_SYSCTL` set because MPTCP fails to initialize
without it. I have `CONFIG_EPOLL` set because my `vido`-based test harness uses
DHCPCD, and my version of DHCPCD requires epoll capabilities.

The process for debugging this sort of thing is not too difficult, although it
may seem daunting:

1. You need some sort of stack trace, frequently from the kernel log or from the
   output of the program that failed.
2. Google will be of no use, because *nobody* encounters errors that occur when
   you strip as many features out of your kernel as possible :)
3. Go straight to the source of what failed, and find where the error message or
   stack trace is produced. Likely you'll find a reference to some feature
   subsystem of the kernel which has a configuration option.
4. Grep through `.config` to find the (commented out) switch that you probably
   ought to enable. Add it to a file in `etc/*.frag`, re-generate your
   `.config`, and rebuild the kernel.

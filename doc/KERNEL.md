Kernel
======

Kernel development is a new world and it's worth documenting.

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

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

A better way is to merge fragments of configurations on top of the alldefconfig.
Currently I have several fragments in my `etc/` folder.

- `vido.frag` - requirements for vido
- `debug.frag` - debugging options
- `mptcp.frag` - configuration of MPTCP

From the root of the linux directory, we can build a configuration as follows:

```bash
scripts/kconfig/merge_config.sh \
    arch/x86/configs/kvm_guest.config \
    ../thesis/etc/*.frag
```

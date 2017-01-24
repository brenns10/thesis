Emacs
=====

A reference to the commands that I find useful navigating through the kernel
code. I use Spacemacs, and my configuration may always be found at
my [dotfiles][] repository.

UI
--

- `SPC t f` - show the 80 column guide

Tags
----

- `, g g` - when cursor is on a tag (e.g. function name), jumps to the
  definition. When on the definition, pops open a Helm dialog containing usages.
- `, g G` - same as above but opens in another window
- `, g r` - find references to the tag on point using a helm dialog
- `, g l` - show tags defined in this file
- `, g i` - show tags used in this function
- `, g s` - search for a tag

You can navigate these jumps with `C-o` to go back. More comprehensively, you
can use `, g n` to go to the (n)ext in the jump stack, and `, g p` to go to the
(p)revious in the jump stack. You can see the jump stack with `, g S`

- `M-]` - find usages and dump them into a buffer rather than a helm box. You
  can use `M-n` and `M-p` to move through these (similar to compile errors)

Completions
-----------

The completion box pops up automatically as you type. Scroll with `C` plus vim
nav keys. According to the docs, `C-d` should show docs for completions, but it
does not.

- `C-M-/` this neat one seems to filter the popup box, highlighting matches
- `C-/` this opens a helm box with the completions

Compilation
-----------

I can generally use the projectile compile function:

- `SPC p c` - compile project. set the command to `make -jN` where N is the
  number of processors/worker threads you want while building.
- `SPC e n` - next error
- `SPC e p` - prev error

[dotfiles]: https://github.com/brenns10/dotfiles

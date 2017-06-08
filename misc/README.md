MISC
====

This is a directory you can probably ignore.

patches contains some patches I used to fix a few bugs I encountered in the
kernel while I was working (unrelated to my path manager). They aren't used to
create the release configuration, just for debug/development.

python contains a modified Python package file for Arch Linux. At the time I
started this project, there was a bug in Python 3.5 which prevented vido from
working properly for my debugging/development system. This directory contains a
patch which was in the upstream versions (but unreleased at the time) so that I
could use vido. The fix was released in 3.6 and now it's unnecessary.

#!/bin/sh
#
# Fix for using iperf3 within virtual machines run with vido!
#
# Due to some funky business regarding the v9fs (used to access the host fs) and
# the unlink + ftruncate system calls used in iperf3, iperf3 will fail to run on
# the client, citing that it could not create a stream (No such file or
# directory). The reason is almost certainly very interesting, but ultimately
# not relevant. We can work around it by mounting our own ramfs at /tmp, so that
# when iperf3 tries to make its own ramfs, it will get our tmpfs, rather than
# talking to v9fs and in turn talking to the host OS.
#
# This email references the unlink followed by X problem in V9, and it seems
# that the fix is not ready:
# https://lkml.org/lkml/2016/6/22/358
#
# Additionally, this GitHub issue proposes the same fix:
# https://github.com/01org/cc-oci-runtime/issues/152
# However, I came up with the same fix independently :D
#
mount -t ramfs -o size=256M ramfs /tmp

AWS Build Machine
=================

Since I needed a Ubuntu machine to build debian kernel packages, I got an AWS
instance. Here's the script to get started:

    sudo apt update
    sudo apt upgrade
    sudo apt install build-essential git kernel-package fakeroot \
        libncurses5-dev libssl-dev ccache
    git clone -b dynamic_detour --single-branch --depth 16 \
        https://github.com/brenns10/mptcp.git

    # from my machine
    scp ~/repos/mptcp/.config AWS:mptcp/

    # in tmux on AWS
    make oldconfig  # just to be sure
    make -j 3 deb-pkg LOCALVERSION=-custom

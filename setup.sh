#!/bin/sh
# To be run on Mininet Ubuntu 14.04 VM after unpacking the tar.

sudo dpkg -i tmp/*.deb

sude apt update -y
sudo apt install -y python3-pip libnl-genl-3-dev openvpn iperf3
sudo pip3 install psutil

# Compile everything freshly on VM.
make -C src clean
make -C src all

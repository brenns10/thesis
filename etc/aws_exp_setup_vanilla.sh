#!/bin/bash
# Run as root. Does not activate MPTCP kernel.
cd

export DEBIAN_FRONTEND=noninteractive
TARNAME=vm.tar

# We'll use the same tarball as the VMs but we won't use the bundled setup.sh
echo Downloading vm tarball...
wget -q https://brenns10.keybase.pub/$TARNAME
chmod a+rx $TARNAME
chmod a+x .
echo Extracting vm tarball...
sudo -u ubuntu tar xf $TARNAME -C ~ubuntu

echo Updating package database...
apt update -q
echo Upgrading packages...
apt upgrade -y -q
echo Installing required packages...
apt install -y -q build-essential python3-pip libnl-genl-3-dev openvpn iperf3 tmux libconfig-dev
echo Installing Python packages...
pip3 install psutil

echo Not bothering with the MPTCP kernel, have fun with vanilla TCP

echo Building tools...
sudo -u ubuntu make -C ~ubuntu/src clean
sudo -u ubuntu make -C ~ubuntu/src all

echo Adding ssh keys...
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDEupr15Lbq8jFBca/tXhydvD2nKQ/vWnxXzOndG7TqKGy53mtlgR6VzaV4WR3blrLdDG223a64VlQaj00xm+8e/eAn+IRH3RpV2ZvFT+BdZmej8E4y0sSlkiCw2sjtyKiGu0Pyk2HKbA8njG+aVsJ5YSQVwBBP1nEqKoMItvXzZwQJQ09SCeklT5zugcJz+frGFifjz1I6bs7Hb9vNa7hNi79JjJ1rNoeANkBmunW20+M7hMOuNjGWl47XGDlew7tn3vc2Eiiohf0cyrueBPq63Y7tMEfhmyCEPfakkjg5idt3soRGKCBqyoVuYyEIOJSTnuGBkThZteGHLlpKvMVz stephen@greed_2013-09-26" >> ~ubuntu/.ssh/authorized_keys

echo Completed successfully! Shutting down...
shutdown -h now

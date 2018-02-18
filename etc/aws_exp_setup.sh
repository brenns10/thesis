#!/bin/bash
# Run as root. Activates MPTCP kernel.
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
echo Installing custom kernel...
dpkg -i ~ubuntu/tmp/*.deb

echo Setting default kernel...
SUBMENU=$(egrep -o -m 1 "gnulinux-advanced[0-9a-zA-Z-]+" /boot/grub/grub.cfg)
BOOT_OPTION=$(egrep -o -m 1 "gnulinux-4.1.38-custom-advanced[0-9a-zA-Z-]+" /boot/grub/grub.cfg)
sed -i.bak "s/#\?GRUB_DEFAULT.*/GRUB_DEFAULT=\"$SUBMENU>$BOOT_OPTION\"/g" /etc/default/grub
update-grub

echo Building tools...
sudo -u ubuntu make -C ~ubuntu/src clean
sudo -u ubuntu make -C ~ubuntu/src all

echo Adding ssh keys...
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDEupr15Lbq8jFBca/tXhydvD2nKQ/vWnxXzOndG7TqKGy53mtlgR6VzaV4WR3blrLdDG223a64VlQaj00xm+8e/eAn+IRH3RpV2ZvFT+BdZmej8E4y0sSlkiCw2sjtyKiGu0Pyk2HKbA8njG+aVsJ5YSQVwBBP1nEqKoMItvXzZwQJQ09SCeklT5zugcJz+frGFifjz1I6bs7Hb9vNa7hNi79JjJ1rNoeANkBmunW20+M7hMOuNjGWl47XGDlew7tn3vc2Eiiohf0cyrueBPq63Y7tMEfhmyCEPfakkjg5idt3soRGKCBqyoVuYyEIOJSTnuGBkThZteGHLlpKvMVz stephen@greed_2013-09-26" >> ~ubuntu/.ssh/authorized_keys
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDE29+4kwdzCHhh/deeYYD8WcJchfD4IAq6m/E3XqDmS/4dgg7QzZk26gCdHQGcbUYRbYhtSnOG4ItkLBbM0u72YKyZ8VTtSeFFbvwBhgQqFUHgnxkyZCuUodJTTIwQBcE6feFbm0/StWJnpHis8Uvgjh/aunFYLJCZu9vIfgyLWPVIMpwItH2uMflTe9tmbp5KQyegtede4IkiUsThh5CslO+PnwVLhUfMvBc82Rtv866AM8UZXYqhYIgqwPuGC6r1mUfiaBS1VEwJYNfrvlAO3eOzWdVCYThMRhjvG72T0S/2HpkNHnpIx6BMG3lGpNxXIvogIRxQjB/KBSDTTeRT stephen@pride" >> ~ubuntu/.ssh/authorized_keys
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC6a5+MF5MBTH9F3Q5cxmitRJrhsWk/ND2KBrH2Lk2ymeCHuNY8CtXNM3qK+18IBmk4A+L/sOY9xeoSmJwpCBkeyF1Cwu664lEbWfNdnPR03MKP3O89WVBkWfkRWoxlrBpPQH78RajqBqkqUpqaJtwtwPAHhZXzCa0Q4WbHJFgq/3MsJ/yf23twBHGZB4Q4xSKkHoDS6Q6G43lZR7lQZLUKoqeGLHcJ0ojIH1dIWiYRN5+R5p3jYjFi6pgZt/Q3B1KaAAhYKVO4UUdYS3VNMTrlGFmgOVf+QniXX8HjL74ZmvgXfGDYm0QdgZllCAzIcvHDt5lusvXLA73SKgN767Glz6dcdiRGN8MgDl7RasT4FnEYUAUEmMyZJ1LnY/ljxeJzF2Yjj+Eob37qn9gECQJOIv1yG4mmv75pN8CSmIq+PZ8KU0XP+Rro6jnBE60HX9I7/nRKE12QWm6AvwVH1MbPbkeqb5Hvkw9CstazwRCStifJM14QXGX9RiemZUgk6/D37YcKctjdFRBsaBKNTg2HiHacJRrj4/KK+piO0etb7va+C3p6LELTzjvslMZbX3VSEmKXqUoIbva6Q4cY4HJX8xIud7B2cFkanA1K0eU4hFXWHzDg5OowbnAG8HjL61IUbdUk2SDA7vVkDVon6cLxFD+0RzuDfk7tDa9iv0ewlQ== stephen@greed:2017-05-10" >> ~ubuntu/.ssh/authorized_keys

echo Setting congestion control to lia
sysctl -w net.ipv4.tcp_congestion_control=lia

echo Completed successfully! Shutting down...
shutdown -h now

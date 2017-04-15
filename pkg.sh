#!/usr/bin/sh
make -C src clean
rm -f vm.tar
tar cf vm.tar \
	src/* \
	etc/* \
	tmp/linux-firmware-image.deb \
	tmp/linux-image.deb \
	setup.sh
echo Package created!

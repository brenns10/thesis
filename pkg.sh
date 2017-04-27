#!/usr/bin/sh
make -C src clean
rm -f vm.tar
tar cf vm.tar \
	src/* \
	etc/* \
	tmp/* \
	setup.sh
echo Package created!

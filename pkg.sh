#!/usr/bin/sh
make -C src clean
rm -f vm.tar
tar cJf vm.tar.xz \
	src/* \
	etc/* \
	tmp/* \
	setup.sh
echo Package created!

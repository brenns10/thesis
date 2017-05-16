#!/usr/bin/sh
make -C src clean
rm -f vm.tar

FILES="src/** etc/** tmp/** setup.sh"
tar cf vm.tar $FILES
sha256sum $FILES vm.tar > sha256sums.txt

echo Package created!
echo Manifest in sha256sums.txt

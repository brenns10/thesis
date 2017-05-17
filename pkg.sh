#!/usr/bin/sh
make -C src clean
rm -f vm.tar

FILES="src/** etc/** tmp/** setup.sh"
tar cvf vm.tar $FILES
sha256sum $FILES > sha256sums.txt
tar -xOf vm.tar | sha256sum >> sha256sums.txt

echo
echo Package created!
echo Manifest in sha256sums.txt

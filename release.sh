#!/bin/bash

if [ "$1" == "" ]; then
	echo "Usage: $0 version"
	exit 1
fi
version=$1

rm -rf release

echo "Ensure you've updated the version in debian/changelog file."
read

make builddeb

pushd server-modules
find -iname "*.pyo" -delete
./zip.sh
popd

mkdir release 

mv server-modules/*.zip release
mv ../koo*deb release

tar jcvf release/koo-$version.tar.bz2 Koo

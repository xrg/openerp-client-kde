#!/bin/bash

make builddeb

pushd server-modules
find -iname "*.pyo" -delete
./zip.sh
popd

mkdir release 

mv server-modules/*.zip release
mv ../koo*deb release


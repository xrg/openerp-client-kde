#!/bin/sh

if [ -z "$1" ]; then
	echo "You must provide an iReport directory."
	exit
fi
directory=$1

rm -I $(ls *.jar | grep -v postgresql)

cp $directory/ireport/modules/ext/*.jar .

cp $directory/ireport/libs/xalan.jar .

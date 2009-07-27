#!/bin/bash

if [ -z "$1" ]; then
	echo "Syntax: ./import-translations.sh launchpad-url"
	exit 1
fi

pushd Koo/l10n

url="$1"

appdir=$(pwd)
tmpdir=$(mktemp -d)

echo "TMP DIR: $tmpdir"

pushd $tmpdir
wget $url
tar zxvf *.tar.gz

for file in $(find -iname "koo-*.po" | grep -v "koo-es" | grep -v "koo-ca"); do
	lang=$(echo $file | cut -d "-" -f 2 | cut -d "." -f 1)
	cp $file $appdir/$lang.po
done

rm -r $tmpdir

popd

popd

#!/bin/sh

# Creates one zip file for each module

list=$(find $2 -iname "__terp__.py" | awk '{system("dirname "$1)}')

for i in $list; do
	echo $i
	zip -r $i.zip $i
done


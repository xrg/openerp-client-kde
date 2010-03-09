#!/bin/bash


function print_log()
{
	current_tag=$1
	current_rev=$2
	previous_tag=$3
	previous_rev=$4

	log=$(bzr log -r$previous_rev..$current_rev | grep -v "^revno: " | grep -v "^committer: " | grep -v "^branch nick: " | grep -v "^timestamp: " | grep -v "^----------------------" | grep -v "^message:" | grep -v "^tags:" | sed 's/^  /- /g')

	log=$(echo "$log" | sed 's_\#\(.\+\)_https://bugs.launchpad.net/openobject-client-kde/+bug/\1_g')

	title="Changelog from $previous_tag (r$previous_rev) to $current_tag (r$current_rev):"
	echo $title
	printf "%${#title}s\n" | sed 's/ /=/g'
	echo
	echo "Koo Fixes:"
	echo "----------"
	echo "$log" | grep -iv 'jasper' | grep -i 'fix'
	echo
	echo "Koo Improvements:"
	echo "-----------------"
	echo "$log" | grep -iv 'jasper' | grep -iv 'fix'
	echo
	echo "Jasper Reports Fixes:"
	echo "---------------------"
	echo "$log" | grep -i 'jasper' | grep -i 'fix'
	echo
	echo "Jasper Reports Improvements:"
	echo "----------------------------"
	echo "$log" | grep -i 'jasper' | grep -iv 'fix'
}

all_tags=$(bzr tags | sort -k 2 -n -r)

current_tag='trunk'
current_rev=$(bzr log -l1 | grep "^revno: " | cut -d " " -f 2)
for current in $(echo "$all_tags" | sed 's/ \+/#/g'); do
	previous_tag=$(echo "$current" | cut -d '#' -f 1)
	previous_rev=$(echo "$current" | cut -d '#' -f 2)
	print_log $current_tag $current_rev $previous_tag $previous_rev
	current_tag=$previous_tag
	current_rev=$previous_rev
	exit 0
done

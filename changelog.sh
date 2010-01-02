#!/bin/bash

last_tag=$(bzr tags | head -1)
tag=$(echo "$last_tag" | awk '{print $1}')
rev=$(echo "$last_tag" | awk '{print $2}')

echo "Changelog since $tag (r$rev):"
log=$(bzr log -r$rev.. | grep -v "^revno: " | grep -v "^committer: " | grep -v "^branch nick: " | grep -v "^timestamp: " | grep -v "^----------------------" | grep -v "^message:" | sed 's/^  /-/g')

echo "Koo Fixes:"
echo "$log" | grep -iv 'jasper' | grep -i 'fix'
echo
echo "Koo Improvements:"
echo "$log" | grep -iv 'jasper' | grep -iv 'fix'
echo
echo "Jasper Reports Fixes:"
echo "$log" | grep -i 'jasper' | grep -i 'fix'
echo
echo "Jasper Reports Improvements:"
echo "$log" | grep -i 'jasper' | grep -iv 'fix'

#!/bin/sh
cat ${1:-/dev/stdin} | grep 'merge time' | awk -v ORS="," '{print $4}'
echo ""

#!/bin/bash
file="${1:?}"

last="$(cat checksums/$file 2> /dev/null)"
current="$(md5sum $file)"

[ "$last" == "$current" ]

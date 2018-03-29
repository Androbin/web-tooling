#!/bin/bash
file="${1:?}"

mkdir -p "$(dirname checksums/$file)"
md5sum "$file" > "checksums/$file"

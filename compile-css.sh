#!/bin/bash
file="${1:?}"

DIR="$(cd "$(dirname "$0")" && pwd)"

if "$DIR"/checksum-read.sh "src/$file"; then
  exit 0
fi

mkdir -p "$(dirname tmp/$file)"
python3 -m csscompressor "src/$file" > "tmp/$file.min"
mkdir -p "$(dirname bin/$file)"

if ! cmp -s "tmp/$file.min" "bin/$file"; then
  mv "tmp/$file.min" "bin/$file"
  echo "$file"
fi

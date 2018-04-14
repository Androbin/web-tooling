#!/bin/bash
file="${1:?}"

DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$(dirname tmp/$file)"
cp "src/$file" "tmp/$file.tr"

if ! "$DIR"/compile-includes.sh "$file"; then
  exit 0
fi

tr '\r' '\n' < "tmp/$file.tr" > "tmp/$file"
htmlmin --keep-optional-attribute-quotes "tmp/$file" "tmp/$file.min"

mkdir -p "$(dirname bin/$file)"

if ! cmp -s "tmp/$file.min" "bin/$file"; then
  mv "tmp/$file.min" "bin/$file"
  echo "$file"
fi

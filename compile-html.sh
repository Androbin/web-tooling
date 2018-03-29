#!/bin/bash
file="${1:?}"

DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$(dirname tmp/$file)"
cp "src/$file" "tmp/$file.tr"

directives_raw=$(grep -ho '<!--#include "[^"]\+"-->' "tmp/$file.tr")
mapfile -t directives <<< "$directives_raw"
dependencies=()
dirty=false

for directive in "${directives[@]}"; do
  [[ ${directive} =~ ^'<!--#include "'([^\"]+)'"-->'$ ]]
  
  path_raw="${BASH_REMATCH[1]}"
  
  if [[ "$path_raw" == css/* ]] || [[ "$path_raw" == js/* ]]; then
    path="bin/$path_raw"
  else
    path="src/$path_raw"
  fi
  
  dependency="$directive~$path"
  dependencies+=("$dependency")
  
  if ! "$DIR"/checksum-read.sh "$path"; then
    dirty=true
  fi
done

if ! "$DIR"/checksum-read.sh "tmp/$file.tr"; then
  dirty=true
  "$DIR"/checksum-write.sh "tmp/$file.tr"
fi

if [[ "$dirty" == false ]]; then
  exit 0
fi

for dependency in "${dependencies[@]}"; do
  IFS='~' dependency=($dependency)
  directive="${dependency[0]}"
  path="${dependency[1]}"
  include_raw=$(tr '\n' '\r' < "$path")
  include=$(echo "$include_raw" | sed 's~\(&\|\\\)~\\\1~g')
  sed -i -- "s~$directive~$include~" "tmp/$file.tr"
done

tr '\r' '\n' < "tmp/$file.tr" > "tmp/$file"
htmlmin --keep-optional-attribute-quotes "tmp/$file" "tmp/$file.min"

mkdir -p "$(dirname bin/$file)"

if ! cmp -s "tmp/$file.min" "bin/$file"; then
  mv "tmp/$file.min" "bin/$file"
  echo "$file"
fi

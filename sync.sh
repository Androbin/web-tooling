#!/usr/bin/env bash
"$DIR"/mount.sh

function foo() {
  for file in "$@"; do
    if [ -e bin/"$file" ]; then
      printf '\r%sUploading: %s' "$(tput el)" "$file"
      mkdir -p sftp/"$(dirname "$file")"
      cp --preserve=timestamps bin/"$file" sftp/"$file"
    elif [ -e sftp/"$file" ]; then
      printf '\r%sCleaning: %s' "$(tput el)" "$file"
      rm sftp/"$file"
    fi
  done

  printf '\r%s' "$(tput el)"
}

export -f foo

xargs -r bash -c 'foo "$@"' _

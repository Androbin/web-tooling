#!/usr/bin/env bash
error=0

for file in "$DIR"/sanity.d/*.sh; do
  "$file" || error=$?
done

exit "$error"

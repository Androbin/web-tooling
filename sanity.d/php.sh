#!/usr/bin/env bash
error=0

shopt -s nullglob

for file in src/**/*.php; do
  php -l "$file" > /dev/null || error=$?
done

exit "$error"

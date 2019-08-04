#!/usr/bin/env bash
"$DIR"/mount.sh

rsync -LrstW --no-compress --progress --delete --exclude private bin/ sftp/ | grep -E '^deleting|[^/]$|^$' | grep -v 'sending incremental file list'

if [ ! -d bin/private ]; then
   exit 0
fi

if [ "$1" = "unsafe" ]; then
  safety_flags=""
else
  safety_flags="--dry-run"
fi

echo '# unsafe'
rsync -LrstW --no-compress --progress --delete $safety_flags --iconv=utf-8,utf-8 bin/private/ sftp/private/ | grep -E '^deleting|[^/]$|^$' | grep -v 'sending incremental file list'

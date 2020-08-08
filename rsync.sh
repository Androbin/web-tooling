#!/usr/bin/env bash
"$DIR"/mount.sh || exit

rsync_grep() {
  rsync "$@" | grep -E '^deleting|[^/]$|^$' | grep -v 'sending incremental file list'
}

flags=(-LrstW --no-compress --progress --delete)
safe_flags=(--exclude private)

rsync_grep "${flags[@]}" "${safe_flags[@]}" bin/ sftp/

if [ ! -d bin/private ]; then
   exit 0
fi

unsafe_flags=(--iconv=utf-8,utf-8)

if [ "$1" != "unsafe" ]; then
  flags=(--dry-run)
fi

echo '# unsafe'
rsync_grep "${flags[@]}" "${unsafe_flags[@]}" bin/private/ sftp/private/

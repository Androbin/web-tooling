#!/usr/bin/env bash
"$DIR"/mount.sh
{ "$DIR"/compile.py 2>&1 1>&3 3>&- | "$DIR"/sync.sh; } 3>&1 1>&2 | cat -

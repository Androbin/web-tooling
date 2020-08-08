#!/usr/bin/env bash
"$DIR"/sanity.sh || exit
"$DIR"/mount.sh || exit
"$DIR"/compile.py | "$DIR"/sync.sh

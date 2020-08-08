#!/usr/bin/env bash
"$DIR"/mount.sh || exit
"$DIR"/compile.py | "$DIR"/sync.sh

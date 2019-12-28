#!/usr/bin/env bash
"$DIR"/mount.sh
"$DIR"/compile.py | "$DIR"/sync.sh

#!/usr/bin/env bash
set -u

export DIR="$(dirname "$(readlink -f "$0")")"
PWD="$(readlink -f "$(pwd)")"

pushd "$PWD" > /dev/null
"$DIR"/"$1".sh "${@:2}"
popd > /dev/null

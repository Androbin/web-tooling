#!/usr/bin/env bash
if mountpoint -q sftp; then
  exit 0
fi

if [ "$1" = "iso" ]; then
  encoding_flags=""
else
  encoding_flags="-o modules=iconv,from_code=utf-8,to_code=utf-8"
fi

config=($(cat config/sftp))
host="${config[0]}"
pass="${config[1]}"
remotePath="${config[2]}"
localPath=sftp

echo "$pass" | sshfs -o password_stdin $encoding_flags "$host"@ssh.strato.de:"$remotePath" "$localPath"

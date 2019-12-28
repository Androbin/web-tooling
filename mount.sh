#!/usr/bin/env bash
if mountpoint -q sftp; then
  exit 0
fi

if [ "$1" = "iso" ]; then
  encoding_flags=()
else
  encoding_flags=("-o" "modules=iconv,from_code=utf-8,to_code=utf-8")
fi

config=($(cat config/sftp))
host="${config[0]}"
user="${config[1]}"
pass="${config[2]}"
remotePath="${config[3]}"
localPath=sftp

if [ "$1" = "unsafe" ]; then
  curlftpfs "$user":"$pass"@"$host" "$localPath"
else
  echo "$pass" | sshfs -o password_stdin "${encoding_flags[@]}" "$user"@"$host":"$remotePath" "$localPath"
fi

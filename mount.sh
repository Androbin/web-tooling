#!/usr/bin/env bash
if mountpoint -q sftp; then
  exit 0
fi

config=($(cat config/sftp))
host="${config[0]}"
user="${config[1]}"
pass="${config[2]}"
remotePath="${config[3]}"
localPath=sftp

flags=()

if [ "$1" != "iso" ]; then
  flags+=(-o modules=iconv,from_code=utf-8,to_code=utf-8)
fi

if [ "$1" = "unsafe" ]; then
  curlftpfs "$user":"$pass"@"$host" "$localPath"
else
  flags+=(-o password_stdin)
  echo "$pass" | sshfs "${flags[@]}" "$user"@"$host":"$remotePath" "$localPath"
fi

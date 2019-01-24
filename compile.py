#!/usr/bin/env python3
from binascii import hexlify
from csscompressor import compress as csscompress
from glob import glob
from hashlib import md5
from htmlmin import minify as htmlmin
from itertools import chain
from jsmin import jsmin
import os
import pickle
import re
import sys
from types import SimpleNamespace

try:
  with open('meta.bin', 'rb') as file:
    meta = pickle.load(file)
except FileNotFoundError:
  meta = SimpleNamespace()
  meta.digest = dict()
  meta.deps = set()

def xglob(include, exclude=[]):
  include = set(chain(*(glob('src/' + x, recursive=True) for x in include)))
  exclude = set(chain(*(glob('src/' + x, recursive=True) for x in exclude)))
  return set(map(lambda x: x[4:], include - exclude))

all_docs = xglob(
  ['**/*.html', '**/*.htm'],
  ['html/**/*.html', 'html/**/*.htm']
)
all_assets = xglob(
  ['**/*.css', '**/*.js', '**/*.json']
)

def calc_digest(path):
  hash_md5 = md5()

  with open(path, "rb") as file:
    hash_md5.update(file.read())

  return hash_md5.digest()

digest = {path: calc_digest('src/' + path) for path in (all_docs | all_assets)}

def has_changed(path):
  return path not in meta.digest or digest[path] != meta.digest[path]

def get_changed(all_files):
  return set(path for path in all_files if has_changed(path))

changed_docs = get_changed(all_docs)
changed_assets = get_changed(all_assets)

deps_assets = set(dep[0] for dep in meta.deps if dep[1] in changed_assets)
changed_docs |= all_docs.intersection(deps_assets)

def process(paths):
  for path in paths:
    ext = path[path.rfind('.'):]

    with open('src/' + path, 'r') as file:
      raw = file.read()

    if ext in ['.css']:
      processed = csscompress(raw)
    elif ext in ['.js', '.json']:
      processed = jsmin(raw, quote_chars="'\"`")
    else:
      processed = process_doc(path, raw)

    os.makedirs(os.path.dirname('bin/' + path), exist_ok=True)

    with open('bin/' + path, 'w+') as file:
      file.write(processed)

    print(path)

def process_doc(pathSelf, raw):
  return htmlmin(
    process_includes(pathSelf, raw),
    remove_comments=True,
    remove_optional_attribute_quotes=False,
  )

def process_includes(pathSelf, rawSelf):
  directives = re.finditer(r'<!--#include "/?([^"]+)"-->', rawSelf)

  for match in directives:
    directive = match.group(0)
    path = match.group(1)

    is_asset = path.split('/', 1)[0] in ['css', 'js']
    path = 'bin/' + path if is_asset else 'src/' + path

    with open(path, 'r') as file:
      raw = file.read()

    rawSelf = rawSelf.replace(directive, raw)
    meta.deps.add((pathSelf, path))

  return rawSelf

process(changed_assets)
process(changed_docs)

meta.digest.update(digest)

with open('meta.bin', 'wb') as file:
  pickle.dump(meta, file, pickle.HIGHEST_PROTOCOL)
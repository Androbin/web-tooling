#!/usr/bin/env python3
from binascii import hexlify
from csscompressor import compress as csscompress
from glob import iglob
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

def xglob(prefix, include, exclude=[]):
  include = set(chain(*(iglob(prefix + x, recursive=True) for x in include)))
  exclude = set(chain(*(iglob(prefix + x, recursive=True) for x in exclude)))
  return set(map(lambda x: x[len(prefix):], include - exclude))

all_docs = xglob('src/',
  ['**/*.html', '**/*.htm'],
  ['html/**/*.html', 'html/**/*.htm']
)
all_assets = xglob('src/',
  ['**/*.css', '**/*.js', '**/*.json'],
  ['html/**/*.html', 'html/**/*.htm']
)

def calc_digest(path):
  hash_md5 = md5()

  with open(path, "rb") as file:
    hash_md5.update(file.read())

  return hash_md5.digest()

digest = {path: calc_digest('src/' + path) for path in (all_docs | all_assets | {'.htaccess'})}

def has_changed(path):
  return path not in meta.digest or digest[path] != meta.digest[path]

def get_changed(all_files):
  return set(path for path in all_files if has_changed(path))

changed_docs = get_changed(all_docs)
changed_assets = get_changed(all_assets)
changed_htaccess = has_changed('.htaccess')

deps_assets_old = set()

while True:
  deps_assets = set(dep[0] for dep in meta.deps if dep[1] in changed_assets)

  if deps_assets == deps_assets_old:
    break

  changed_docs |= all_docs.intersection(deps_assets)
  changed_assets |= all_assets.intersection(deps_assets)
  changed_htaccess |= '.htaccess' in deps_assets
  deps_assets_old = deps_assets

def suffix_path(path, suffix):
  ext = path[path.rfind('.'):]
  return path[:-len(ext)] + '-' + suffix + ext

def digestify_path(path):
  return suffix_path(path, digest[path].hex()[:7])

def cleanup_path(path):
  return suffix_path(path, r'[a-z0-9]' * 7)

def process(paths):
  for path in paths:
    ext = path[path.rfind('.'):]

    with open('src/' + path, 'r') as file:
      raw = file.read()

    if ext in ['.css']:
      processed = csscompress(raw)
      pathOut = digestify_path(path)
      cleanup = [cleanup_path(path)]
    elif ext in ['.js', '.json']:
      processed = process_js(path, raw)
      pathOut = digestify_path(path)
      cleanup = [cleanup_path(path)]
    else:
      processed = process_doc(path, raw)
      pathOut = path
      cleanup = []

    for dirt in xglob('bin/', cleanup):
      os.remove('bin/' + dirt)
      print(dirt, file=sys.stderr)

    os.makedirs(os.path.dirname('bin/' + pathOut), exist_ok=True)

    with open('bin/' + pathOut, 'w+') as file:
      file.write(processed)

    print(path)
    print(pathOut, file=sys.stderr)

def process_js(pathSelf, raw):
  references = re.finditer(r'/[*][*]/(["\']/?)([^"\']+)(["\'])/[*][*]/', raw)

  for match in references:
    reference = match.group(0)
    prefix = match.group(1)
    path = match.group(2)
    suffix = match.group(3)

    raw = raw.replace(reference, prefix + digestify_path(path) + suffix)
    meta.deps.add((pathSelf, path))

  return jsmin(raw, quote_chars="'\"`")

def process_doc(pathSelf, raw):
  dependencies = re.finditer(r'(href|src)="/([^"]*\.(css|js|json))"', raw)

  for match in dependencies:
    dependency = match.group(0)
    prop = match.group(1)
    path = match.group(2)

    raw = raw.replace(dependency, prop + '="/' + digestify_path(path) + '"')
    meta.deps.add((pathSelf, path))

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

    ext = path[path.rfind('.'):]
    is_asset = ext in ['.css', '.js', '.json']
    rawPath = 'bin/' + digestify_path(path) if is_asset else 'src/' + path

    with open(rawPath, 'r') as file:
      raw = file.read()

    rawSelf = rawSelf.replace(directive, raw)
    meta.deps.add((pathSelf, path))

  return rawSelf

def process_htaccess():
  with open('src/.htaccess', 'r') as file:
    raw = file.read()

  preloads = re.finditer(r'(Header add Link "<https?://[^/]+/)((css|js)/[^>]+)(>; rel=preload; as=[a-z]+" env=X_[A-Z_]+)', raw)

  for match in preloads:
    preload = match.group(0)
    prefix = match.group(1)
    path = match.group(2)
    suffix = match.group(4)
    raw = raw.replace(preload, prefix + digestify_path(path) + suffix)
    meta.deps.add(('.htaccess', path))

  with open('bin/.htaccess', 'w+') as file:
    file.write(raw)

  print('.htaccess')
  print('.htaccess', file=sys.stderr)

process(changed_assets)
process(changed_docs)

if changed_htaccess:
  process_htaccess()

meta.digest.update(digest)

with open('meta.bin', 'wb') as file:
  pickle.dump(meta, file, pickle.HIGHEST_PROTOCOL)

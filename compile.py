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

asset_ext = ['css', 'htaccess', 'htm', 'html', 'js', 'json', 'php']
all_assets = xglob('src/', ['**/*.' + ext for ext in asset_ext], ['**/html/**/*'])

def calc_digest(path):
  hash_md5 = md5()

  with open(path, "rb") as file:
    hash_md5.update(file.read())

  return hash_md5.digest()

digest = {path: calc_digest('src/' + path) for path in (all_assets)}

def has_changed(path):
  return path not in meta.digest or digest[path] != meta.digest[path]

def get_changed(all_files):
  return set(path for path in all_files if has_changed(path))

changed_assets = get_changed(all_assets)

deps_assets_old = set()

while True:
  deps_assets = set(dep[0] for dep in meta.deps if dep[1] in changed_assets)

  if deps_assets == deps_assets_old:
    break

  changed_assets |= all_assets.intersection(deps_assets)
  deps_assets_old = deps_assets

def resolve_path(pathSelf, path):
  return os.path.relpath(os.path.join('/', os.path.dirname(pathSelf), path), start = '/')

def suffix_path(path, suffix):
  ext = path[path.rfind('.'):]
  return path[:-len(ext)] + '-' + suffix + ext

def digestify_path(path, pathResolved=None):
  if pathResolved is None:
    pathResolved = path

  return suffix_path(path, digest[pathResolved].hex()[:7])

def cleanup_path(path):
  return suffix_path(path, r'[a-z0-9]' * 7)

def process(paths):
  for path in paths:
    processed, pathOut, cleanup = process_raw(path)

    for dirt in xglob('bin/', cleanup):
      os.remove('bin/' + dirt)
      print(dirt)

    os.makedirs(os.path.dirname('bin/' + pathOut), exist_ok=True)

    with open('bin/' + pathOut, 'w+') as file:
      file.write(processed)

    print(path, file=sys.stderr)
    print(pathOut)

def process_raw(path):
  ext = path[path.rfind('.'):]

  with open('src/' + path, 'r') as file:
    raw = file.read()

  processed = raw
  pathOut = path
  cleanup = []

  if ext in ['.css']:
    processed = process_css(path, raw)
    pathOut = digestify_path(path)
    cleanup = [cleanup_path(path)]
  elif ext in ['.js', '.json']:
    processed = process_js(path, raw)
    pathOut = digestify_path(path)
    cleanup = [cleanup_path(path)]
  elif ext in ['.htaccess']:
    processed = process_htaccess(path, raw)
  elif ext in ['.htm', '.html']:
    processed = process_html(path, raw)

  return processed, pathOut, cleanup

def process_css(pathSelf, raw):
  raw = process_includes(pathSelf, raw)
  return csscompress(raw)

def process_js(pathSelf, raw):
  raw = process_paths(pathSelf, raw)
  return jsmin(raw, quote_chars="'\"`")

def process_html(pathSelf, raw):
  dependencies = re.finditer(r'(href|src)="(/?[^"/][^":]*\.(css|js|json))"', raw)

  for match in dependencies:
    dependency = match.group(0)
    prop = match.group(1)
    path = match.group(2)

    pathResolved = resolve_path(pathSelf, path)

    if pathResolved not in all_assets:
      print("# Skipping:", pathResolved, file=sys.stderr)
      continue

    pathDigest = digestify_path(path, pathResolved)
    raw = raw.replace(dependency, prop + '="' + pathDigest + '"')
    meta.deps.add((pathSelf, pathResolved))

  raw = process_includes(pathSelf, raw)
  raw = process_paths(pathSelf, raw)
  return htmlmin(raw,
    remove_comments=True,
    remove_optional_attribute_quotes=False,
  )

def process_paths(pathSelf, raw):
  references = re.finditer(r'''/[*][*]/(["'])([^"\']+)(["'])/[*][*]/''', raw)

  for match in references:
    reference = match.group(0)
    prefix = match.group(1)
    path = match.group(2)
    suffix = match.group(3)

    pathResolved = resolve_path(pathSelf, path)
    pathDigest = digestify_path(path, pathResolved)
    raw = raw.replace(reference, prefix + pathDigest + suffix)
    meta.deps.add((pathSelf, path))

  return raw

def process_includes(pathSelf, rawSelf):
  directives = re.finditer(r'<!--#include "([^"]+)"-->', rawSelf)

  for match in directives:
    directive = match.group(0)
    path = match.group(1)

    pathResolved = resolve_path(pathSelf, path)
    raw = process_raw(pathResolved)[0]
    rawSelf = rawSelf.replace(directive, raw)
    meta.deps.add((pathSelf, pathResolved))

  return rawSelf

def process_htaccess(pathSelf, raw):
  preload_ext = ['css', 'js', 'json']
  preloads = re.finditer(r'(Header add Link "<https?://[^/]+)(/[^>]+\.(' + '|'.join(preload_ext) + r'))(>; rel=preload; as=[a-z]+" env=X_[A-Z_]+)', raw)

  for match in preloads:
    preload = match.group(0)
    prefix = match.group(1)
    path = match.group(2)
    suffix = match.group(4)

    pathResolved = resolve_path('/', path)
    pathDigest = digestify_path(path, pathResolved)
    raw = raw.replace(preload, prefix + pathDigest + suffix)
    meta.deps.add((pathSelf, path))

  return raw

changed_assets = sorted(changed_assets)
process(changed_assets)

meta.digest.update(digest)

with open('meta.bin', 'wb') as file:
  pickle.dump(meta, file, pickle.HIGHEST_PROTOCOL)

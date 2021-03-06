#!/bin/bash

function error_usage()
{
  usage='Usage: make_installers [options...]

Options:
  -d, --dest-dir [DIRECTORY] - destination directory of the created package
  -f, --force - make package even if the repository contains local changes
  -i, --installers [INSTALLERS] - comma-separated list of installers to create
    - possible values for installers: "windows", "linux", "macos", "zip", "all"
    - default: "zip"
    - example: -i "windows,zip" creates a Windows installer and a ZIP package for manual install
    - "all" creates all installers - note that creating a Windows installer may not be possible on *nix systems
    - unrecognized values are silently ignored
  -o, --no-docs - do not generate documentation
  -h, --help - display this help and exit'
  
  if [ -z "$1" ]; then
    printf '%s\n' "${1:-$usage}"
  else
    printf 'Error: %s\n\n%s\n' "$1" "${2:-$usage}"
  fi
  
  exit 1
} 1>&2


destination_dirpath='None'
force_if_dirty='False'
installers='"zip"'
generate_docs='True'


while [[ "${1:0:1}" = "-" && "$1" != "--" ]]; do
  case "$1" in
  -d | --dest-dir ) shift; destination_dirpath='r"'"$1"'"';;
  -f | --force ) force_if_dirty='True';;
  -i | --installers ) shift; installers='"'"$1"'"';;
  -o | --no-docs ) generate_docs='False';;
  -h | --help ) error_usage;;
  * ) [[ "$1" ]] && error_usage "unknown argument: $1";;
  esac

  shift
done

[[ "$1" = "--" ]] && shift


gimp -i --batch-interpreter="python-fu-eval" -b '
import sys
import os

plugin_dirpath = os.path.join(gimp.directory, "plug-ins - Export Layers")
utils_dirpath = os.path.join(plugin_dirpath, "utils")

sys.path.append(plugin_dirpath)
sys.path.append(os.path.join(plugin_dirpath, "export_layers"))
sys.path.append(os.path.join(plugin_dirpath, "export_layers", "pygimplib"))
sys.path.append(utils_dirpath)

import make_installers

make_installers.main(destination_dirpath='"$destination_dirpath"', force_if_dirty='"$force_if_dirty"', installers='"$installers"', generate_docs='"$generate_docs"')

pdb.gimp_quit(0)
'

#!/bin/bash

set -e

bzr=$1
dir=$2

bzr branch "$bzr" "$dir"
cd $dir
git init
bzr fast-export --plain | git fast-import
git add -A
git reset --hard

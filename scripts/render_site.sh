#!/bin/zsh

mkdir -p dist/site
uv run render -m s
cp -r dist/site/. site/
cd site && bundle exec jekyll serve

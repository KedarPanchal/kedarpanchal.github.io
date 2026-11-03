#!/bin/zsh

mkdir -p dist/resume
uv run render -m r
cd dist/resume && pdflatex -interaction=nonstopmode resume.tex

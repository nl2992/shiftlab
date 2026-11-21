#!/bin/sh
# Build the Paper 4 TMLR draft.
set -e
cd "$(dirname "$0")"
latexmk -pdf -file-line-error -interaction=nonstopmode -halt-on-error main.tex

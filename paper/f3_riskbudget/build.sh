#!/bin/sh
cd "$(dirname "$0")" && python3 make_tables.py && pdflatex -interaction=nonstopmode main.tex >/dev/null && bibtex main >/dev/null; pdflatex -interaction=nonstopmode main.tex >/dev/null; pdflatex -interaction=nonstopmode main.tex | grep -iE "Overfull|Error|undefined|Output"

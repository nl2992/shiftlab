#!/bin/sh
# Regenerate tables from committed result files, then build main.pdf (pdflatex + bibtex).
cd "$(dirname "$0")" && python3 make_tables.py && python3 make_screen_tables.py && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex >/dev/null 2>&1; grep -iE "Overfull|Underfull|Warning|Error|undefined|Output written" main.log | sort | uniq -c

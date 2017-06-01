LaTeX
=====

This directory contains LaTeX sources for my presentation and paper. The
`figures` subdirectory contains PDF versions of the figures (many copied from
`data` and others created via Google Drive). The `refs` subdirectory contains
some references, for convenience.

The following commands should be sufficient to completely build both
presentation and paper, using the correct magic combinations of `pdflatex` and
`bibtex`, etc.

    latexmk -pdf presentation
    latexmk -pdf paper

If `latexmk` is not available, `pdflatex` / `bibtex` / `pdflatex` / `pdflatex`
should do the trick.

If you want to get rid of all generated files safely, a nifty way to do it is

    git clean -xif .

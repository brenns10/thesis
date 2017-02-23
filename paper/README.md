Paper
=====

Building this requires GNU Make, pdflatex, bibtex, latexmk. The Makefile is
designed so that parts of the thesis can be extracted out into separate papers
so that I can create PDFs of individual sections.

For example, the related work section is written in `frag_related_work.tex`, but
it goes into both `paper.pdf`, and it also can be put into its own file,
`frag_related_work.pdf`.

`make` builds the main paper, `paper.pdf`.

`make parts` builds the fragments, `frag_SOMETHING.pdf`.

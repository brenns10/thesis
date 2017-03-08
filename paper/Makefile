FRAGS=$(wildcard frag_*.tex)
PARTS=$(patsubst frag_%.tex,part_%.pdf,$(FRAGS))

.PHONY: all clean
all: paper.pdf
parts: $(PARTS)

clean:
	latexmk -CA
	rm -f $(PARTS)
	rm -f $(patsubst %.pdf,%.pdf,$(PARTS))
	rm -f $(patsubst %.pdf,%.aux,$(PARTS))
	rm -f $(patsubst %.pdf,%.fls,$(PARTS))
	rm -f $(patsubst %.pdf,%.fdb_latexmk,$(PARTS))
	rm -f $(patsubst %.pdf,%.log,$(PARTS))

paper.tex: _header.tex paper_body.tex $(FRAGS)
	cat _header.tex paper_body.tex > paper.tex

%.pdf: %.tex
	latexmk -pdf -pdflatex="pdflatex -interaction=nonstopmode" -use-make $<

part_%.tex: frag_%.tex _header.tex _part_top.tex _part_bottom.tex
	cat _header.tex _part_top.tex $< _part_bottom.tex > $@

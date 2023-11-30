LATEX := xelatex
BUILDDIR := pdf
TEXDIR := tex

TEX_FILES := $(addprefix $(TEXDIR)/,*.tex)

PDF_FILES := $(BUILDDIR)/literature_review.pdf

LATEX_INTERMEDIATE := $(BUILDDIR)/

.PHONY: clean clean-bcf

$(BUILDDIR)/%.bcf: $(TEXDIR)/%.tex
	TEXINPUTS="./tex/:" ; $(LATEX) -synctex=1 -interaction=nonstopmode --shell-escape -output-directory=$(BUILDDIR) $<

$(BUILDDIR)/%.bbl: $(BUILDDIR)/%.bcf $(TEXDIR)/%.tex $(TEXDIR)/references.bib
	biber --input-directory $(TEXDIR) $<

$(BUILDDIR)/%.toc: $(TEXDIR)/%.tex
	TEXINPUTS="./tex/:" ; $(LATEX) -synctex=0 -interaction=nonstopmode --shell-escape -output-directory=$(BUILDDIR) $<

$(BUILDDIR)/%.pdf: $(TEXDIR)/%.tex $(BUILDDIR)/%.bbl $(BUILDDIR)/%.toc $(TEX_FILES)
	TEXINPUTS="./tex/:" ; $(LATEX) -synctex=1 -interaction=nonstopmode --shell-escape -output-directory=$(BUILDDIR) $<

$(BUILDDIR):
	mkdir $(BUILDDIR)

all: $(PDF_FILES) $(BUILDDIR)


clean-bcf:
	-rm $(BUILDDIR)/*.bcf $(BUILDDIR)/*.blg

clean:
	-rm $(BUILDDIR)/*.aux $(BUILDDIR)/*.log $(BUILDDIR)/*.out $(BUILDDIR)/*.toc

info:
	@echo $(TEXINPUTS)
	@ls -l $(TEX_FILES) pdf/*.b?? pdf/*.toc pdf/*.pdf

doc: docbook doxygen

docbook:
	cd src && docbook2html -o ../html koo.docbook && cp *.png ../html
	
doxygen:
	cd doxygen && doxygen koo.doxyfile

.PHONY: doxygen docbook

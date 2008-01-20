doc: docbook doxygen

docbook:
	cd src && docbook2html -o ../html ktiny.docbook && cp *.png ../html
	
doxygen:
	cd doxygen && doxygen ktiny.doxyfile

.PHONY: doxygen docbook

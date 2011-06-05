build: $(patsubst %.ui,%.py,$(wildcard *.ui))

%.py: %.ui
	pyuic4 -o $@ $<


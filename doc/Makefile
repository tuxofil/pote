.PHONY: all clean

all: $(patsubst %.dot, %.png, $(wildcard *.dot))

%.png: %.dot
	dot -T png $< > $@

clean:
	rm -f -- *.png

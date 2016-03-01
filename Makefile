.PHONY: all doc lint test clean start

all:

doc:
	$(MAKE) -C doc

lint:
	pep8 bin/poted
	pylint -rn bin/poted || :
	pep8 pote
	pylint -rn pote || :

test:
	$(MAKE) -C test

clean:
	find pote/ -type f -name '*.py[co]' -delete
	$(MAKE) -C test $@
	$(MAKE) -C doc $@

start:
	PYTHONPATH=. ./bin/poted --verbose

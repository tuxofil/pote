.PHONY: all clean

export PYTHONPATH = ../../

all: clean
	python -m unittest -v test_storage
	python -m unittest -v queue_storage
	python -m unittest -v archive_storage
	python -m unittest -v main

clean:
	rm -f -- *.pyc *.pyo
	rm -rf poted poted.log

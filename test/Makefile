TESTS = unit-tests

.PHONY: all clean $(TESTS)

all: $(TESTS)

clean: $(TESTS)

$(TESTS):
	$(MAKE) -C $@ $(MAKECMDGOALS)

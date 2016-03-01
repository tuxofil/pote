import random
import sys


sys.stdout.write('%s started\n' % __name__)
if random.choice([True, False]):
    sys.stdout.write('%s done\n' % __name__)
else:
    sys.stderr.write('%s crashed\n' % __name__)
    sys.exit(1)

import random
import sys
import time


sys.stdout.write('%s started\n' % __name__)
time.sleep(20)
if random.choice([True, False]):
    sys.stdout.write('%s done\n' % __name__)
else:
    sys.stderr.write('%s crashed\n' % __name__)
    sys.exit(1)

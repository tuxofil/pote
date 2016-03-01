import sys
import time


sys.stdout.write('%s started\n' % __name__)
time.sleep(70)
raise Exception

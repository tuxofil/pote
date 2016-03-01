import sys
import time


sys.stdout.write('%s started\n' % __name__)
time.sleep(5)
raise Exception

import sys
import time


sys.stdout.write('%s started\n' % __name__)
sys.stderr.write('%s: warning\n' % __name__)
time.sleep(80)
sys.stdout.write('%s done\n' % __name__)

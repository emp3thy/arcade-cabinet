import os
import sys

# cad/ is a plain directory of scripts, not a package: put it on the path so
# the tests import fusion_run the way the command line runs it.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# isort:skip_file

# make pythonpath the upper directory relative to the location of this file
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from utils.system import is_production
from utils.logging import log

import faulthandler

# Setup the fault handler so we can send SIGABRT and get a stack trace
if not is_production():
    faulthandler.enable()

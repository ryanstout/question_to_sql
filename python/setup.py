# make pythonpath the upper directory relative to the location of this file
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .utils.logging import log

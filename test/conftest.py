import os
import sys


# for pytest to see imports from /src
def setup_path():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


setup_path()

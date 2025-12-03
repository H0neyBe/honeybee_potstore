import sys
import os

try:
    import cowrie._version as cowrie_version
    __version__ = getattr(cowrie_version, '__version__', '2.9.0')
except ModuleNotFoundError:
    # When running without pip install -e ., use static version
    __version__ = "2.9.0"

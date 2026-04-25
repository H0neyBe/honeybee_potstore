"""WebTrap - Vulnerable Web Application Honeypot for HoneyBee.

This package can be used in two ways:

1. As a standalone web honeypot (see ``standalone.py``)::

       python standalone.py

2. As an importable module to be plugged into another WSGI app::

       from webtrap import create_app
       app = create_app()

The honeypot intentionally simulates a vulnerable website (fake admin
panels, login pages, API endpoints, file upload pages and misconfigured
services).  Every interaction is captured, fingerprinted and forwarded
to a HoneyBee Node over JSON-line TCP at ``127.0.0.1:9100`` - the same
protocol used by Cowrie and HonnyPotter.
"""

from .app import create_app
from .config import WebTrapConfig
from .forwarder import HoneyBeeForwarder

__all__ = ["create_app", "WebTrapConfig", "HoneyBeeForwarder"]
__version__ = "1.0.0"

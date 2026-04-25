"""Route blueprints for WebTrap."""

from .admin import bp as admin_bp
from .api import bp as api_bp
from .login import bp as login_bp
from .misconfig import bp as misconfig_bp
from .upload import bp as upload_bp
from .catchall import bp as catchall_bp

ALL_BLUEPRINTS = [
    login_bp,
    admin_bp,
    api_bp,
    upload_bp,
    misconfig_bp,
    # catchall MUST be last - it owns "/" and the wildcard.
    catchall_bp,
]

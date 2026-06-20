"""
Package exports for authentication and authorisation.
"""

from .authentication import Authentication
from .authorisation import Authorisation

# Instantiate default instances for shared use across the application
authentication = Authentication()
authorisation = Authorisation()

__all__ = ["Authentication", "Authorisation", "authentication", "authorisation"]

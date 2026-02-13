"""
WSGI config for Tropical Corner.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tropicalcorner.settings.prod")

application = get_wsgi_application()

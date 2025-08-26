"""
WSGI config for snow_predict project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'snow_predict.settings')

application = get_wsgi_application()

"""
WSGI config for recomendacao project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os, sys

sys.path.append(os.path.dirname(__file__).replace('\\','/'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recomendacao.settings")

from django.core.handlers.wsgi import WSGIHandler
application =  WSGIHandler()

from django.core.wsgi import get_wsgi_application
_application = get_wsgi_application()

from django.conf import settings

def application(environ, start_response):
    script_name = environ.get('SCRIPT_NAME', '')
    settings.STATIC_URL = script_name + '/static/'
    settings.FILES_URL = script_name + '/files/'
    return _application(environ, start_response)

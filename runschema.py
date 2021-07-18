# This file mainly exists to allow python setup.py test to work.
# flake8: noqa
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner
from django.core import management

os.environ['DJANGO_SETTINGS_MODULE'] = 'dj_rest_auth.tests.settings'
test_dir = os.path.join(os.path.dirname(__file__), 'dj_rest_auth')
sys.path.insert(0, test_dir)



def generateschema():
    if hasattr(django, 'setup'):
        django.setup()
    management.call_command('generateschema')


if __name__ == '__main__':
    generateschema()

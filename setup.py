#!/usr/bin/env python

import os
import re

from setuptools import find_packages, setup

here = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(here, 'README.md'))
long_description = f.read().strip()
f.close()


def get_version():
    """Extract version from dj_rest_auth/__version__.py."""
    with open('dj_rest_auth/__version__.py', 'r', encoding="utf8") as f:
        version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='dj-rest-auth',
    version=get_version(),
    author='iMerica',
    author_email='imichael@pm.me',
    url='https://github.com/iMerica/dj-rest-auth',
    description='Authentication and Registration in Django Rest Framework',
    license='MIT',
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=[
        'django',
        'rest',
        'auth',
        'registration',
        'rest-framework',
        'api',
    ],
    install_requires=[
        'Django>=2.2',
        'djangorestframework>=3.11',
    ],
    extras_require={
        'with_social': [
            'django-allauth>=0.42.0',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Session',
    ],
)

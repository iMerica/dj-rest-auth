#!/usr/bin/env python

import os

from setuptools import find_packages, setup

here = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(here, 'README.md'))
long_description = f.read().strip()
f.close()


about = {}
with open('dj_rest_auth/__version__.py', 'r', encoding="utf8") as f:
    exec(f.read(), about)

setup(
    name='dj-rest-auth',
    version=about['__version__'],
    author='iMerica',
    author_email='imichael@pm.me',
    url='http://github.com/iMerica/dj-rest-auth',
    description='Authentication and Registration in Django Rest Framework',
    license='MIT',
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='django rest auth registration rest-framework django-registration api',
    zip_safe=False,
    install_requires=[
        'Django>=2.0',
        'djangorestframework>=3.7.0',
    ],
    extras_require={
        'with_social': ['django-allauth>=0.40.0,<0.45.0'],
    },
    tests_require=[
        'coveralls>=1.11.1',
        'django-allauth==0.42.0',
        'djangorestframework-simplejwt==4.6.0',
        'responses==0.12.1',
        'unittest-xml-reporting==3.0.4',
    ],
    test_suite='runtests.runtests',
    include_package_data=True,
    python_requires='>=3.5',
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)

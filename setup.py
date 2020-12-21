#!/usr/bin/env python

import os

from setuptools import find_packages, setup

here = os.path.dirname(os.path.abspath(__file__))
f = open(os.path.join(here, 'README.md'))
long_description = f.read().strip()
f.close()


setup(
    name='dj-rest-auth',
    use_scm_version={"version_scheme": "post-release"},
    setup_requires=["setuptools_scm"],
    author='iMerica',
    author_email='imichael@pm.me',
    url='http://github.com/jazzband/dj-rest-auth',
    description='Authentication and Registration in Django Rest Framework',
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
        'with_social': ['django-allauth>=0.40.0,<0.43.0'],
    },
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

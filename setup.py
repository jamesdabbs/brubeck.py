#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='brubeck',
    version='0.0.1.029',
    description='Django-powered database of topological information',

    author='James Dabbs',
    author_email='james.dabbs@gmail.com',
    url='https://github.com/jamesdabbs/brubeck',

    packages=find_packages(exclude=['tests.*', 'tests']),
    include_package_data=True,  # declarations in MANIFEST.in

    install_requires=['Django >=1.4'],

    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
)

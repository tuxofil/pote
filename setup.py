#!/usr/bin/env python

import setuptools


def get_version():
    """
    Fetch current version from debian/changelog file.

    :rtype: string
    """
    with open('debian/changelog') as fdescr:
        return fdescr.readline().split()[1].strip('()')


setuptools.setup(
    name = 'pote',
    version = get_version(),
    description = 'Python Online Test Executor.',
    author = 'Aleksey Morarash',
    author_email = 'aleksey.morarash@gmail.com',
    packages = setuptools.find_packages(exclude=('test')),
    provides = ['pote'],
    requires = [],
    include_package_data = True,
    zip_safe = True,
    license = 'Public Domain',
    platforms = 'Platform Independent',
    classifiers = ['Development Status :: 2 - Pre-Alpha',
                   'License :: Public Domain',
                   'Intended Audience :: Developers',
                   'Operating System :: OS Independent',
                   'Natural Language :: English',
                   'Topic :: Software Development'])

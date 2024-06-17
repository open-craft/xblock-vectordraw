"""Setup for vectordraw XBlock."""


import os

from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}


setup(
    name='vectordraw-xblock',
    version='0.4.0',
    description='vectordraw XBlock',   # TODO: write a better description.
    url='https://github.com/open-craft/xblock-vectordraw',
    license='AGPLv3',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Affero General Public License v3',
    ],
    packages=[
        'vectordraw',
    ],
    install_requires=[
        'XBlock',
        'xblock-utils',
    ],
    entry_points={
        'xblock.v1': [
            'vectordraw = vectordraw.vectordraw:VectorDrawXBlock',
        ]
    },
    package_data=package_data("vectordraw", ["static", "public", "templates"]),
)

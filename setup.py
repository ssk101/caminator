#!/usr/bin/env python3

import setuptools

with open('readme.md', 'r') as fh:
  long_description = fh.read()

setuptools.setup(
    name = 'caminator',
    version = '1.0.0',
    author = 'Steel Sky Software',
    author_email = 'steelskysoftware@gmail.com',
    description = 'picamera2 streamer',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/steelskysoftware/caminator',
    packages = setuptools.find_packages(),
    classifiers = [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable'
    ],
    python_requires='>=3'
)
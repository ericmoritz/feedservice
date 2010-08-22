#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='feedservice',
      version='0.1',
      description="""feedservice provides a
little feed caching service to ensure that external
feeds will be fetched in a timely manner.""",
      author='Eric Moritz',
      author_email='eric@themoritzfamily.com',
      url='',
      scripts=['bin/feedjanitor'],
      packages=find_packages(),
     )

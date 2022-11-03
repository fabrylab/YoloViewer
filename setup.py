# -*- coding: utf-8 -*-
# setup.py

from setuptools import setup
setup(name='YoloViwer',
      version="0.1",
      description='',
      author='Johannes Bartl, Sebastian Bohle',
      author_email='',
      packages=['pylonBasler'],
      python_requires=">=3.6.*",
      install_requires=[
            "numpy",
            "pypylon",
            "psutil",
            "matplotlib",
            "tensorflow==2.5.3",
            "imageio",
            "flask",
            "tifffile",
            "clickpoints",
            "Pillow"

      ],
      # dependency_links= ["https://github.com/basler/pypylon/releases/download/1.4.0/pypylon-1.4.0-cp37-cp37m-linux_armv7l.whl"]
      )

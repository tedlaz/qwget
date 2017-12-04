from setuptools import setup

# python setup.py sdist --formats=gztar,zip

setup(name='python-qwget',
      version='0.6',
      license='GPL',
      description='Easy download',
      author='Ted Lazaros',
      author_email='tedlaz@gmail.com',
      packages=['qwget'],
      package_data={'': ['qwget.png']},
      include_package_data=True,
      entry_points={
          'gui_scripts': ['qwget=qwget.qwget:main']
      },
      )
